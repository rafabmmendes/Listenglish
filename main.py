import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro: API Key não encontrada.")

DIFICULDADES = {
    "Begginer": "Short phrases, simple greetings.",
    "basic": "Daily routines, present tense.",
    "intermediate": "Past and future with connectors.",
    "advanced": "Phrasal verbs and idioms.",
    "professional": "Business context.",
    "fluenty": "Native level nuances."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO REFORMULADA (BLINDADA) ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        
        # Geramos uma chave baseada no tempo para garantir unicidade absoluta
        unique_id = int(time.time() * 1000)
        
        md = f"""
            <div style="margin: 10px 0;">
                <small>{label}</small><br>
                <audio key="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Erro no áudio.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None

# --- 4. FUNÇÃO DE GERAÇÃO (UNIFICADA) ---
def proxima_pergunta():
    # Limpa estados anteriores
    st.session_state.feedback = None
    st.session_state.frase_pt = None
    st.session_state.frase_en = None
    
    # Cria uma semente única para a IA
    seed = f"{time.time()}-{random.randint(1,9999)}"
    prompt = (f"Seed: {seed}. Level: {st.session_state.nivel}. "
              f"Format: Phrase: [English] | Translation: [Portuguese]")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0
        ).choices[0].message.content
        
        if "|" in res:
            st.session_state.frase_en = res.split("|")[0].split("Phrase:")[-1].strip(" []")
            st.session_state.frase_pt = res.split("|")[1].split("Translation:")[-1].strip(" []")
            # Muda a chave do áudio para forçar o navegador a recarregar
            st.session_state.audio_key += 1 
    except:
        st.error("Erro ao gerar frase.")

# --- 5. INTERFACE ---
st.set_page_config(page_title="Coach Inglês", layout="centered")

with st.sidebar:
    st.title("Configurações")
    st.session_state.nivel = st.selectbox("Nível:", LISTA_NIVEIS)
    st.write(f"🏆 Streak: {st.session_state.test_streak}")
    if st.button("♻️ Reiniciar Tudo"):
        st.session_state.clear()
        st.rerun()

st.title("🎙️ Prática de Tradução Oral")

# BOTÃO DE TROCA
if st.button("⏭️ PRÓXIMA PERGUNTA", type="primary"):
    proxima_pergunta()
    st.rerun()

# GERAR SE ESTIVER VAZIO
if st.session_state.frase_pt is None:
    proxima_pergunta()

# EXIBIÇÃO
if st.session_state.frase_pt:
    st.info(f"### Traduza: {st.session_state.frase_pt}")
    
    # PLAYER DE PORTUGUÊS (ID DINÂMICO)
    # A key no markdown e o cache buster forçam a mudança
    play_audio(
        st.session_state.frase_pt, 
        lang='pt', 
        autoplay=True, 
        label=f"Desafio #{st.session_state.audio_key}"
    )

    st.divider()

    # MICROFONE
    audio_bytes = mic_recorder(
        start_prompt="🎤 Gravar Tradução", 
        stop_prompt="⏹️ Analisar", 
        key=f"mic_{st.session_state.audio_key}"
    )

    if audio_bytes:
        with st.spinner("Analisando..."):
            # Transcrição Whisper
            transcript = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes['bytes']), 
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
            
            # Avaliação Llama
            f_prompt = f"Student said '{transcript}' for '{st.session_state.frase_en}'. Correct in PT-BR. If correct, start with CORRETO."
            feedback = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f_prompt}]
            ).choices[0].message.content
            
            st.session_state.feedback = {"falado": transcript, "texto": feedback}

    # RESULTADOS
    if st.session_state.feedback:
        st.write(f"🗣️ **Você disse:** {st.session_state.feedback['falado']}")
        st.write(f"📝 **Feedback:** {st.session_state.feedback['texto']}")
        
        st.success(f"✅ **Gabarito:** {st.session_state.frase_en}")
        # Áudio em Inglês (Manual)
        play_audio(st.session_state.frase_en, lang='en', label="Pronúncia correta")
        
        if "CORRETO" in st.session_state.feedback['texto'].upper():
            st.session_state.test_streak += 1
        else:
            st.session_state.test_streak = 0

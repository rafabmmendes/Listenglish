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
    st.error("Erro: API Key não encontrada nos Secrets do Streamlit.")

DIFICULDADES = {
    "Begginer": "Short phrases (2-3 words), very simple greetings.",
    "Basic": "Sentences in present tense about daily life.",
    "Intermediate": "Past and future tenses with connectors.",
    "Advanced": "Complex sentences with phrasal verbs.",
    "Professional": "Business English and workplace scenarios.",
    "Fluenty": "Native-level slang and idioms."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO COM "CACHE BUSTER" (PARA MUDAR SEMPRE) ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        
        # ID único para forçar o navegador a recarregar o som
        unique_id = f"{time.time()}_{random.randint(1, 1000)}"
        
        md = f"""
            <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 10px;">
                <small>{label} ({lang.upper()})</small><br>
                <audio id="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'modo' not in st.session_state: st.session_state.modo = 'Prática'
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0
if 'audio_inicial_ok' not in st.session_state: st.session_state.audio_inicial_ok = False

# --- 4. FUNÇÃO PARA GERAR NOVA PERGUNTA ---
def proxima_pergunta():
    st.session_state.frase_en = None
    st.session_state.frase_pt = None
    st.session_state.feedback = None
    st.session_state.audio_inicial_ok = False
    st.session_state.audio_key += 1 # Muda a key do microfone e do áudio
    
    seed = f"{time.time()}-{random.randint(1, 9999)}"
    prompt = (f"Seed: {seed}. Level: {st.session_state.nivel}. "
              f"Instructions: {DIFICULDADES[st.session_state.nivel]}. "
              f"Generate a UNIQUE sentence. Format: Phrase: [English] | Translation: [Portuguese]")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0
        ).choices[0].message.content
        
        if "|" in res:
            st.session_state.frase_en = res.split("|")[0].split("Phrase:")[-1].strip(" []")
            st.session_state.frase_pt = res.split("|")[1].split("Translation:")[-1].strip(" []")
    except:
        st.error("Erro na conexão com a IA.")

# --- 5. INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.title("🏆 Painel de Controlo")
    
    # Seleção de Modo
    st.session_state.modo = st.radio("Escolha o Modo:", ["Prática", "Teste de Maestria"])
    
    # Seleção de Nível
    st.session_state.nivel = st.selectbox("Nível de Dificuldade:", LISTA_NIVEIS)
    
    st.divider()
    
    # EXIBIÇÃO DO TESTE DE NÍVEL
    if st.session_state.modo == "Teste de Maestria":
        st.subheader("Progresso do Teste")
        st.write(f"Acertos seguidos: **{st.session_state.test_streak} / 5**")
        st.progress(st.session_state.test_streak / 5)
        st.caption("Acerte 5 frases seguidas para subir de nível automaticamente!")
    else:
        st.success("Modo Prática: Treino livre sem pressão.")

    if st.button("♻️ Reiniciar Tudo"):
        st.session_state.clear()
        st.rerun()

# --- 6. CONTEÚDO PRINCIPAL ---
st.title("🎙️ Gemini English Coach")

if st.button("⏭️ GERAR NOVA PERGUNTA", type="primary"):
    proxima_pergunta()
    st.rerun()

# Gerar primeira pergunta automaticamente
if st.session_state.frase_pt is None:
    proxima_pergunta()

if st.session_state.frase_pt:
    st.write(f"**Modo:** {st.session_state.modo} | **Nível:** {st.session_state.nivel}")
    st.info(f"### Como se diz:\n# {st.session_state.frase_pt}")

    # Áudio em Português automático (Cache Buster Ativo)
    if not st.session_state.audio_inicial_ok:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=True, label="Ouvir Desafio")
        st.session_state.audio_inicial_ok = True
    else:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=False, label="Repetir Desafio")

    st.divider()

    # Gravação
    audio_data = mic_recorder(
        start_prompt="🎤 Gravar Tradução", 
        stop_prompt="⏹️ Analisar", 
        key=f"mic_{st.session_state.audio_key}"
    )

    if audio_data:
        with st.spinner("A analisar..."):
            # Whisper Transcrição
            transcript = client.audio.transcriptions.create(
                file=("audio.wav", audio_data['bytes']), 
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
            
            # Llama Avaliação
            f_prompt = f"The student said '{transcript}' for '{st.session_state.frase_en}'. Correct in Portuguese. If correct, start with CORRETO."
            eval_text = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f_prompt}]
            ).choices[0].message.content
            
            st.session_state.feedback = {"falado": transcript, "texto": eval_text}

    # Resultados
    if st.session_state.feedback:
        st.write(f"🗣️ **Você disse:** {st.session_state.feedback['falado']}")
        st.write(f"📝 **Feedback:** {st.session_state.feedback['texto']}")
        
        st.success(f"✅ **Gabarito:** {st.session_state.frase_en}")
        play_audio(st.session_state.frase_en, lang='en', label="Pronúncia Correta")

        # LÓGICA DO TESTE DE NÍVEL
        if "CORRETO" in st.session_state.feedback['texto'].upper():
            if st.session_state.modo == "Teste de Maestria":

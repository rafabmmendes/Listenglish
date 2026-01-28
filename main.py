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
    st.error("Erro: API Key não encontrada nos Secrets.")

DIFICULDADES = {
    "Begginer": "Short phrases (2-3 words), very simple greetings.",
    "basic": "Sentences in present tense about daily life.",
    "intermediate": "Past and future tenses with connectors like 'because'.",
    "advanced": "Complex sentences with phrasal verbs.",
    "professional": "Business English and workplace scenarios.",
    "fluenty": "Native-level slang, idioms, and metaphors."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO COM QUEBRA DE CACHE ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        
        # O cache_buster garante que o áudio mude sempre que a frase mudar
        cache_buster = random.randint(1, 999999)
        
        md = f"""
            <div style="margin: 10px 0; padding: 10px; border-radius: 5px; background-color: #f0f2f6;">
                <small style="color: #555;">{label} ({lang.upper()})</small><br>
                <audio id="audio_{cache_buster}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={cache_buster}" type="audio/mp3">
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
if 'audio_inicial_tocado' not in st.session_state: st.session_state.audio_inicial_tocado = False
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0

# --- 4. FUNÇÃO DE GERAÇÃO ---
def gerar_pergunta():
    st.session_state.frase_en = None
    st.session_state.frase_pt = None
    st.session_state.feedback = None
    st.session_state.audio_inicial_tocado = False
    st.session_state.mic_key += 1
    
    # Seed única para garantir que a IA não repita a frase
    seed = f"{time.time()}-{random.randint(1, 999)}"
    prompt = (f"Seed: {seed}. Level: {st.session_state.nivel}. "
              f"Rule: {DIFICULDADES[st.session_state.nivel]}. "
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
        st.error("Erro ao conectar com a IA.")

# --- 5. INTERFACE ---
st.set_page_config(page_title="Gemini English Coach", page_icon="🎙️")

with st.sidebar:
    st.title("📚 Menu")
    st.session_state.nivel = st.selectbox("Seu Nível Atual:", LISTA_NIVEIS)
    st.session_state.modo = st.radio("Selecione o Modo:", ["Prática", "Teste de Maestria"])
    
    if st.session_state.modo == "Teste de Maestria":
        st.divider()
        st.write(f"🏆 Progresso: **{st.session_state.test_streak}/5**")
        st.progress(st.session_state.test_streak / 5)
        st.caption("Acerte 5 seguidas para subir de nível!")
    
    if st.button("♻️ Resetar Sessão"):
        st.session_state.clear()
        st.rerun()

st.title("🎙️ Gemini English Coach")

# Botão de próxima pergunta
if st.button("⏭️ PRÓXIMA PERGUNTA", type="primary"):
    gerar_pergunta()
    st.rerun()

# Inicialização automática
if st.session_state.frase_pt is None:
    gerar_pergunta()

# EXIBIÇÃO DO DESAFIO
if st.session_state.frase_pt:
    st.subheader("Como se diz isso em inglês?")
    st.info(f"### {st.session_state.frase_pt}")

    # Áudio em Português (O Desafio) - Toca automático 1 vez
    if not st.session_state.audio_inicial_tocado:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=True, label="Ouvindo desafio...")
        st.session_state.audio_inicial_tocado = True
    else:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=False, label="Repetir desafio")

    st.write("---")

    # GRAVAÇÃO
    audio_data = mic_recorder(
        start_prompt="🎤 Falar Tradução", 
        stop_prompt="⏹️ Analisar", 
        key=f"mic_{st.session_state.mic_key}"
    )

    if audio_data:
        with st.spinner("Analisando sua pronúncia..."):
            # 1. Transcrever
            transcript = client.audio.transcriptions.create(
                file=("audio.wav", audio_data['bytes']), 
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
            
            # 2. Avaliar
            f_prompt = f"The student said '{transcript}' to translate '{st.session_state.frase_pt}' into '{st.session_state.frase_en}'. Give feedback in Portuguese. If it's correct, start with the word 'CORRETO'."
            eval_res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f_prompt}]
            ).choices[0].message.content
            
            st.session_state.feedback = {"falado": transcript, "texto": eval_res}

    # RESULTADOS E GABARITO (Só aparecem após falar)
    if st.session_state.feedback:
        st.divider()
        st.markdown(f"**Você disse:** *{st.session_state.feedback['falado']}*")
        st.markdown(f"**Feedback:** {st.session_state.feedback['texto']}")
        
        st.success(f"✅ **Gabarito:** {st.session_state.frase_en}")
        play_audio(st.session_state.frase_en, lang='en', autoplay=False, label="Ouvir pronúncia correta")

        # Lógica de Maestria
        if "CORRETO" in st.session_state.feedback['texto'].upper():
            if st.session_state.modo == "Teste de Maestria":
                st.session_state.test_streak += 1
                if st.session_state.test_streak >= 5:
                    st.balloons()
                    st.success("🎉 PARABÉNS! Você provou sua maestria!")
                    idx = LISTA_NIVEIS.index(st.session_state.nivel)
                    if idx < len(LISTA_NIVEIS) - 1:
                        st.session_state.nivel = LISTA_NIVEIS[idx+1]
                        st.session_state.test_streak = 0
                        st.info(f"Você subiu para o nível: **{st.session_state.nivel}**")
        else:
            if st.session_state.modo == "Teste de Maestria":
                st.error("❌ Erro detectado! O contador de maestria voltou para zero.")
                st.session_state.test_streak = 0

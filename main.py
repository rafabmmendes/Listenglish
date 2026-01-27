import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

# --- 2. FUNÇÕES AUXILIARES ---

def transcrever_audio(audio_bytes):
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3-turbo", 
            response_format="text"
        )
        return transcription
    except Exception as e:
        return None

def chamar_ia(prompt):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro: {e}"

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- 4. FLUXO DE TELAS ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Escolha seu Objetivo")
    obj = st.selectbox("Foco do curso:", ["Business", "Travel", "Social"])
    if st.button("Iniciar Teste ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'teste_nivel'
        st.rerun()

elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste Rápido")
    pergunta = st.radio("Traduza: 'Eu gosto de café'", ["I like coffee", "I likes coffee"])
    if st.button("Finalizar Teste"):
        st.session_state.nivel = "A2" if pergunta == "I like coffee" else "A1"
        st.session_state.step = 'pratica'
        st.rerun()

elif st.session_state.step == 'pratica':
    with st.sidebar:
        st.title("👤 Perfil")
        st.write(f"Nível: **{st.session_state.nivel}**")
        st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
        if st.button("🔄 Reiniciar"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🗣️ Pratique sua Fala")

    if st.button("⏭️ Próxima Pergunta", type="primary"):
        with st.spinner("Gerando..."):
            prompt = f"Crie uma frase curta nível {st.session_state.nivel} sobre {st.session_state.obj_selecionado}. Formato: Phrase: [Inglês] | Translation: [Português]"
            res = chamar_ia(prompt)
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.feedback = None
                st.session_state.texto_falado = None
                st.session_state.mic_key += 1
                st.rerun()

    if st.session_state.aula_atual:

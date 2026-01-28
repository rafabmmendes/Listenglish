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
    st.error("Erro: API Key não configurada nos Secrets.")

DIFICULDADES = {
    "Begginer": "Short phrases, simple greetings.",
    "Basic": "Sentences in present tense about daily life.",
    "Intermediate": "Past and future tenses with connectors.",
    "Advanced": "Complex sentences with phrasal verbs.",
    "Professional": "Business English and workplace scenarios.",
    "Fluenty": "Native-level slang and idioms."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO COM CACHE BUSTER ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        unique_id = f"{time.time()}_{random.randint(1, 1000)}"
        md = f"""
            <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 10px; background-color: #1e1e1e; color: white;">
                <small>{label}</small><br>
                <audio id="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Erro ao carregar som.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel_idx' not in st.session_state: st.session_state.nivel_idx = 0
if 'modo' not in st.session_state: st.session_state.modo = 'Prática'
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0
if 'audio_inicial_ok' not

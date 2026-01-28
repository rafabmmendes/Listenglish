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
    "Basic": "Sentences in present tense about daily life.",
    "Intermediate": "Past and future tenses with connectors.",
    "Advanced": "Complex sentences with phrasal verbs.",
    "Professional": "Business English and workplace scenarios.",
    "Fluenty": "Native-level slang and idioms."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        unique_id = f"{time.time()}_{random.randint(1, 1000)}"
        md = f"""
            <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff;">
                <small style="color: #666;">{label} ({lang.upper()})</small><br>
                <audio id="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel_idx' not in st.session_state: st.session_state.nivel_idx = 0
if 'modo' not in st.session_state: st.session_state.modo = 'Prática'
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0
if 'audio_inicial_ok' not in st.session_state: st.session_state.audio_inicial_ok = False

# Nível atual baseado no índice
nivel_atual = LISTA_NIVEIS[st.session_state.nivel_idx]

# --- 4. FUNÇÃO PARA GERAR NOVA PERGUNTA ---
def proxima_pergunta():
    st.session_state.frase_en = None
    st.session_state.frase_pt = None
    st.session_state.feedback = None
    st.session_state.audio_inicial_ok = False
    st.session_state.audio_key += 1
    seed = f"{time.time()}-{random.randint(1, 9999)}"
    prompt = (f"Seed: {seed}. Level: {nivel_atual}. "
              f"Instructions: {DIFICULDADES[nivel_atual]}. "
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
    st.title("🏆 Maestria")
    st.session_state.modo = st.radio("Modo de Jogo:", ["Prática", "Teste de Maestria"])
    
    st.divider()
    st.write(f"📈 Nível Atual: **{nivel_atual}**")
    
    if st.session_state.modo == "Teste de Maestria":
        st.subheader("Desafio de Nível")
        st.write(f"Sequência: {st.session_state.test_streak} / 5")
        st.progress(st.session_state.test_streak / 5)
        st.caption("Acerte 5 seguidas para desbloquear o próximo nível!")
    else:
        st.info("No modo Prática você treina sem perder sua sequência.")

    if st.button("♻️ Reiniciar Progresso"):
        st.session_state.clear()
        st.rerun()

# --- 6. CONTEÚDO PRINCIPAL

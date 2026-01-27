import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO ---
@st.cache_resource
def load_model():
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = load_model()

# Banco de reserva para quando a cota estourar
FRASES_RESERVA = [
    {"en": "I would like to order a coffee, please.", "pt": "Eu gostaria de pedir um café, por favor."},
    {"en": "Can you show me the way to the hotel?", "pt": "Você pode me mostrar o caminho para o hotel?"},
    {"en": "It is a pleasure to meet you.", "pt": "É um prazer te conhecer."}
]

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- INICIALIZAÇÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'feedback' not in st.session_state: st.session_state.feedback = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    st.write(f"XP: {st.session_state.xp}/100")
    if st.button("🔄 Resetar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA DE TREINO ---
st.title("🗣️ Treino de Fala")

if st.button("✨ Gerar Nova Frase"):
    try:
        seed = random.randint(1, 10000)
        prompt = f"English level {st.session_state.nivel}. Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
        res = model.generate_content(prompt)
        st.session_state.aula_atual = res.text
        st.session_state.feedback = "" 
    except:
        # SE A IA FALHAR (ERRO 429), USA RESERVA
        item = random.choice(FRASES_RESERVA)
        st.session_state.aula_atual = f"Phrase: {item['en']} | Translation: {item['pt']}"
        st.warning("IA em repouso. Usando lição offline para você não parar!")

if st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ingles_correto = texto.split("|")[0].split(":")[-1].strip()
        portugues = texto.split("|")[1].split(":")[-1].strip()
        
        st.subheader("Traduza e Fale:")
        st.info(f"💡 {portugues}")
        
        if st.button("🔊 Ouvir Pronúncia"):
            play_audio(ingles_correto)

        st.write("### 🎤 Grave sua voz:")
        audio_gravado = mic_recorder(start_prompt="Gravar", stop_prompt="Parar", key='recorder')

        if audio_gravado:
            if st.button("🔍 Corrigir minha fala"):
                with st.spinner("Analisando sua voz..."):
                    try:
                        audio_data = {"mime_type": "audio/wav", "data": audio_gravado['bytes']}
                        p_aval = f"Analyze my pronunciation for: '{ingles_correto}'. Be concise in Portuguese."
                        response = model.generate_content([p_aval, audio_data])
                        st.session_state.feedback = response.text
                        st.session_state.xp += 20
                    except:
                        st.error("Cota cheia. Mas sua voz foi gravada! Tente corrigir em 15 segundos.")

        if st.session_state.feedback:
            st.success("Feedback da IA:")
            st.write(st.session_state.feedback)
            st.write(f"**Frase correta:** {ingles_correto}")
    except:
        st.error("Erro ao carregar lição.")

# Lógica automática de Nível Up
niveis = ["A1", "A2", "B1", "B2", "C1"]
if st.session_state.xp >= 100:
    idx = niveis.index(st.session_state.nivel)
    if idx < len(niveis)-1:
        st.session_state.nivel = niveis[idx+1]
        st.session_state.xp = 0
        st.balloons()

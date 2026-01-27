import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- BANCO DE DADOS DE RESERVA (Caso a IA falhe) ---
FRASES_RESERVA = [
    {"en": "I need to check my email.", "pt": "Eu preciso checar meu e-mail."},
    {"en": "Where is the nearest station?", "pt": "Onde fica a estação mais próxima?"},
    {"en": "Could you repeat that, please?", "pt": "Você poderia repetir isso, por favor?"},
    {"en": "I am looking for a new job.", "pt": "Estou procurando um novo emprego."},
    {"en": "Have a great day!", "pt": "Tenha um ótimo dia!"}
]

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

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Progresso")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100)
    st.write(f"XP: {st.session_state.xp}/100")
    if st.button("🔄 Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🏋️ Treino de Inglês")

if st.button("✨ Gerar Nova Lição"):
    with st.spinner("Buscando lição..."):
        try:
            # TENTA USAR A IA
            seed = random.randint(1, 10000)
            prompt = f"Level {st.session_state.nivel} English sentence. Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
            res = model.generate_content(prompt)
            st.session_state.aula_atual = res.text
            st.session_state.xp += 20
        except:
            # SE A IA FALHAR, USA O BANCO DE RESERVA
            item = random.choice(FRASES_RESERVA)
            st.session_state.aula_atual = f"Phrase: {item['en']} | Translation: {item['pt']}"
            st.session_state.xp += 10
            st.info("Nota: Usando lição do banco de reserva (IA em repouso).")

# MOSTRAR A LIÇÃO SEMPRE QUE EXISTIR
if st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ingles = texto.split("|")[0].split(":")[-1].strip()
        portugues = texto.split("|")[1].split(":")[-1].strip()
        
        st.subheader("Como se diz em inglês?")
        st.write(f"💡 *{portugues}*")
        
        if st.button("🔊 Ver Resposta e Ouvir"):
            st.success(ingles)
            play_audio(ingles)
            
            # Lógica de subir nível
            if st.session_state.xp >= 100:
                niveis = ["A1", "A2", "B1", "B2", "C1"]
                idx = niveis.index(st.session_state.nivel)
                if idx < len(niveis)-1:
                    st.session_state.nivel = niveis[idx+1]
                    st.session_state.xp = 0
                    st.balloons()
    except:
        st.error("Erro ao exibir lição. Tente gerar outra.")

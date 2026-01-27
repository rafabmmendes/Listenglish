import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random
import time

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

# --- LÓGICA DE EVOLUÇÃO DE NÍVEL ---
def check_level_up():
    niveis = ["A1", "A2", "B1", "B2", "C1", "C2"]
    if st.session_state.xp >= 100:
        atual = st.session_state.nivel
        if atual in niveis and atual != "C2":
            novo_index = niveis.index(atual) + 1
            st.session_state.nivel = niveis[novo_index]
            st.session_state.xp = 0 # Reseta XP para o novo nível
            st.balloons()
            st.success(f"🎊 PARABÉNS! Você subiu para o nível {st.session_state.nivel}!")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Perfil do Aluno")
    st.metric("Nível Atual", st.session_state.nivel)
    st.write(f"**XP do Nível:** {st.session_state.xp}/100")
    st.progress(st.session_state.xp / 100)
    
    if st.button("🔄 Reiniciar Tudo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---

if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Seu objetivo:", ["Business", "Travel", "Social"])
    if st.button("Iniciar"):
        st.session_state.obj = obj
        st.session_state.step = 'test'
        st.rerun()

elif st.session_state.step == 'test':
    st.title("🎤 Teste Inicial")
    if 'frase_teste' not in st.session_state:
        try:
            res = model.generate_content("Generate 1 short B1 English sentence. Just the sentence.")
            st.session_state.frase_teste = res.text.strip()
        except:
            st.session_state.frase_teste = "I am learning English to improve my career."
    
    play_audio(st.session_state.frase_teste)
    resposta = st.text_input("O que você ouviu?")
    
    if st.button("Avaliar"):
        if len(resposta) > 5:
            # Validação simples para economizar cota da IA
            st.session_state.step = 'practice'
            st.rerun()
        else:
            st.error("Resposta muito curta! Tente novamente.")

elif st.session_state.step == 'practice':
    st.title("🏋️ Prática Diária")
    check_level_up()
    
    if st.button("✨ Nova Lição"):
        try:
            seed = random.randint(1, 5000)
            p = f"Level {st.session_state.nivel} English about {st.session_state.obj}. Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
            res = model.generate_content(p)
            st.session_state.aula_atual = res.text
            st.session_state.xp += 25 # Ganha 25 XP por frase
        except:
            st.error("Cota cheia! Aguarde 10 segundos.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            partes = st.session_state.aula_atual.split("|")
            ing = partes[0].split(":")[-1].strip()
            pt = partes[1].split(":")[-1].strip()
            st.info(f"Traduza: {pt}")
            if st.button("🔊 Ver Resposta"):
                play_audio(ing)
                st.success(ing)

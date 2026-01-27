import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO DE ACESSO ---
# O código tentará usar st.secrets para segurança. 
# Se rodar localmente sem segredos, ele cairá no except.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        key = st.secrets["GOOGLE_API_KEY"]
    else:
        # APENAS para teste local. No GitHub/Streamlit Cloud, use o painel Secrets.
        key = "SUA_CHAVE_AQUI" 
    
    genai.configure(api_key=key)
    # 'gemini-pro' é o modelo com maior compatibilidade global
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")

# --- FUNÇÕES DE SUPORTE ---
def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except Exception as e:
        st.warning("Não foi possível gerar o áudio. Tente novamente.")

# --- ESTADO DO APLICATIVO ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'nivel' not in st.session_state: st.session_state.nivel = 'B1'

# --- INTERFACE (SIDEBAR) ---
st.set_page_config(page_title="LinguistAI", page_icon="🎧")

with st.sidebar:
    st.title("👤 Seu Progresso")
    if 'obj' in st.session_state:
        st.metric(label="Nível Atual", value=st.session_state.nivel)
        st.write(f"🎯 **Foco:** {st.session_state.obj}")
        st.write(f"🔥 **XP:** {st.session_state.xp}")
        progresso = min(st.session_state.xp / 100, 1.0)
        st.progress(progresso)
        st.caption("Ganhe 100 XP para subir de nível!")
    
    if st.button("Reiniciar Aplicativo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- FLUXO DE TELAS ---

# TELA 1: CONFIGURAÇÃO INICIAL
if st.session_state.step == 'setup':
    st.title("🎧 LinguistAI: Treino Auditivo")
    st.subheader("Personalize sua experiência")
    
    obj = st.selectbox("Qual seu objetivo?", ["Business (Trabalho)", "Travel (Viagem)", "Social (Conversação)"])

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO ---
# Tenta pegar a chave do Streamlit Cloud, se não encontrar, usa uma string vazia
try:
    api_key = st.secrets.get("GOOGLE_API_KEY", "SUA_CHAVE_AQUI")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("Erro na API Key. Configure nos Secrets do Streamlit.")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Progresso")
    if 'obj' in st.session_state:
        st.write(f"**Foco:** {st.session_state.obj}")
        st.write(f"**XP:** {st.session_state.xp}")
    if st.button("Reiniciar Aplicativo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELA 1: SETUP ---
if st.session_state.step == 'setup':
    st.title("🎧 LinguistAI")
    obj = st.selectbox("Qual seu objetivo?", ["Business", "Travel", "Social"])
    if st.button("Confirmar e Começar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

# --- TELA 2: PRÁTICA (Onde o botão deve estar) ---
elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    
    # O BOTÃO ESTÁ AQUI:
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("IA criando lição..."):
            try:
                prompt = f"Create a short English sentence for {st.session_state.obj}. Format: Phrase: [English] | Translation: [Portuguese]"
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except Exception as e:
                st.error(f"A IA não respondeu. Verifique sua chave. Erro: {e}")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        texto = st.session_state.aula_atual
        if "|" in texto:
            ingles = texto.split("|")[0].replace("Phrase:", "").strip()
            portugues = texto.split("|")[1].replace("Translation:", "").strip()
            st.write(f"**Como se diz:** {portugues}")
            if st.button("🔊 Ouvir Resposta"):
                play_audio(ingles)
                st.success(f"Inglês: {ingles}")
        else:
            st.write(texto)
            

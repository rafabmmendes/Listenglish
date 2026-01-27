import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ---
try:
    # Busca a chave nos Secrets do Streamlit Cloud
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    genai.configure(api_key=api_key)
    # Modelo Flash: mais rápido e com maior cota gratuita
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de Configuração: {e}")

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("⚠️ O player de áudio falhou.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível", st.session_state.nivel)
    st.write(f"**XP:** {st.session_state.xp}")
    st.progress(min(st.session_state.xp / 100, 1.0))
    if st.button("🔄 Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---

# TELA 1: SETUP
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Seu objetivo:", ["Business (Trabalho)", "Travel (Viagem)", "Social"])
    if st.button("Iniciar Teste de Nível"):
        st.session_state.obj = obj
        with st.spinner("IA preparando desafio..."):
            try:
                # Prompt para frase de teste aleatória
                res = model.generate_content(f"Generate 1 unique English sentence about {obj} for a B1 level test.")
                st.session_state.frase_teste = res.text
            except:
                st.session_state.frase_teste = "I need to check my schedule before the next meeting."
            st.session_state.step = 'test'
            st.rerun()

# TELA 2: TESTE DE NÍVEL
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nível")
    st.write("Ouça e escreva o que entendeu:")
    play_audio(st.session_state.frase_teste)
    
    resposta = st.text_input("Sua resposta:")
    if st.button("Finalizar Teste"):
        with st.spinner("Avaliando..."):
            try:
                # IA define o nível do usuário
                prompt_eval = f"User understood '{resposta}' for the phrase '{st.session_state.frase_teste}'. Return only the CEFR level: A1, A2, B1, B2, or C1."
                result = model.generate_content(prompt_eval).text.strip()
                st.session_state.nivel = result[:2]
            except:
                st.session_state.nivel = "B1" # Fallback
            st.session_state.step = 'practice'
            st.rerun()

# TELA 3: PRÁTICA INFINITA
elif st.session_state.step == 'practice':
    st.title("🏋️ Prática")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("IA criando frase inédita..."):
            try:
                # Uso de seed aleatória para evitar repetição
                seed = random.randint(1, 10000)
                prompt = f"Create a UNIQUE English phrase level {st.session_state.nivel} for {st.session_state.obj}. Seed {seed}. Format: Phrase: [English] | Translation: [Portuguese]"
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except Exception as e:
                st.error("Cota atingida! Aguarde 30 segundos ou tente novamente.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            partes = st.session_state.aula_atual.split("|")
            ingles = partes[0].replace("Phrase:", "").strip()
            portugues = partes[1].replace("Translation:", "").strip()
            
            st.write(f"**Como se diz:** {portugues}")
            if st.button("🔊 Ouvir Resposta"):
                play_audio(ingles)
                st.success(f"**Inglês:** {ingles}")

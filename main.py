import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ---
try:
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro na API Key. Verifique os Secrets.")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível Atual", st.session_state.nivel)
    st.write(f"**XP:** {st.session_state.xp}")
    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELA 1: SETUP ---
if st.session_state.step == 'setup':
    st.title("🚀 Bem-vindo ao LinguistAI")
    obj = st.selectbox("Seu objetivo:", ["Business", "Travel", "Social"])
    if st.button("Começar Teste de Nível"):
        st.session_state.obj = obj
        with st.spinner("Gerando desafio de nível..."):
            # Gera uma frase aleatória para testar o usuário
            seed = random.randint(1, 1000)
            prompt = f"Generate a unique B1 level English sentence about {obj}. Seed: {seed}"
            frase_teste = model.generate_content(prompt).text
            st.session_state.frase_teste = frase_teste
            st.session_state.step = 'test'
            st.rerun()

# --- TELA 2: TESTE DE NÍVEL ---
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nivelamento")
    st.write("Ouça a frase e escreva o que entendeu (em Inglês ou Português):")
    play_audio(st.session_state.frase_teste)
    
    res_user = st.text_input("Sua resposta:")
    if st.button("Avaliar meu Nível"):
        with st.spinner("Analisando..."):
            prompt_aval = f"User heard '{st.session_state.frase_teste}' and wrote '{res_user}'. Grade their CEFR level (A1, A2, B1, B2, C1). Return ONLY the level code."
            nivel_final = model.generate_content(prompt_aval).text.strip()
            st.session_state.nivel = nivel_final
            st.session_state.step = 'practice'
            st.rerun()

# --- TELA 3: PRÁTICA ---
elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("IA criando frase inédita..."):
            # O Segredo para não repetir: usar um número aleatório (seed) no prompt
            seed = random.randint(1, 9999)
            prompt = (f"Create a unique, NEW English sentence for level {st.session_state.nivel} "
                      f"about {st.session_state.obj}. Random seed: {seed}. "
                      f"Format: Phrase: [English] | Translation: [Portuguese]")
            try:
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except:
                st.error("Erro de cota. Tente em 1 minuto.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            ingles = st.session_state.aula_atual.split("|")[0].replace("Phrase:", "").strip()
            portugues = st.session_state.aula_atual.split("|")[1].replace("Translation:", "").strip()
            
            st.subheader("Como se diz:")
            st.info(portugues)
            if st.button("🔊 Ouvir Pronúncia"):
                play_audio(ingles)
                st.success(f"Inglês: {ingles}")

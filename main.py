import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ROBUSTA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Mudamos para o nome de modelo mais estável e universal
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("Chave não encontrada nos Secrets.")
except Exception as e:
    st.error(f"Erro de conexão: {e}")

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível no momento.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.write(f"**Nível:** {st.session_state.nivel}")
    st.write(f"**XP:** {st.session_state.xp}")
    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELA 1: SETUP ---
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Escolha seu objetivo:", ["Business", "Travel", "Social"])
    
    if st.button("Iniciar Teste de Nível"):
        st.session_state.obj = obj
        with st.spinner("Preparando teste..."):
            try:
                seed = random.randint(1, 1000)
                prompt = f"Generate 1 short B1 level English sentence about {obj}. Seed {seed}. Return ONLY the sentence."
                response = model.generate_content(prompt)
                st.session_state.frase_teste = response.text
            except:
                # PLANO B: Se a IA der erro 404 de novo, usamos uma frase fixa para o app não travar
                st.session_state.frase_teste = "I would like to improve my English skills for my future career."
            
            st.session_state.step = 'test'
            st.rerun()

# --- TELA 2: TESTE DE NÍVEL ---
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nivelamento")
    st.info("Ouça a frase abaixo e escreva o que entendeu.")
    
    if 'frase_teste' in st.session_state:
        play_audio(st.session_state.frase_teste)
        
        res_user = st.text_input("Sua resposta (Inglês ou Português):")
        
        if st.button("Avaliar Nível"):
            if res_user:
                with st.spinner("Analisando..."):
                    try:
                        prompt_eval = f"User heard '{st.session_state.frase_teste}' and understood '{res_user}'. Based on CEFR, return only the code: A1, A2, B1, B2 or C1."
                        nivel = model.generate_content(prompt_eval).text.strip()
                        st.session_state.nivel = nivel[:2] # Pega só os 2 primeiros caracteres (ex: B1)
                    except:
                        st.session_state.nivel = "B1" # Nível padrão caso a IA falhe
                    
                    st.session_state.step = 'practice'
                    st.rerun()
            else:
                st.warning("Por favor, escreva algo.")

# --- TELA 3: PRÁTICA ---
elif st.session_state.step == 'practice':
    st.title("🏋️ Treinamento")
    st.success(f"Nível atual: {st.session_state.nivel}")

    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("Criando..."):
            try:
                seed = random.randint(1, 10000)
                prompt = f"Create a UNIQUE English sentence for level {st.session_state.nivel} about {st.session_state.obj}. Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except:
                st.error("Erro na IA. Tente gerar novamente em alguns segundos.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            ingles = st.session_state.aula_atual.split("|")[0].replace("Phrase:", "").strip()
            portugues = st.session_state.aula_atual.split("|")[1].replace("Translation:", "").strip()
            
            st.subheader("Como se diz:")
            st.write(f"💡 *{portugues}*")
            if st.button("🔊 Ouvir Pronúncia"):
                play_audio(ingles)
                st.success(f"**Inglês:** {ingles}")

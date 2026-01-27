import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO ---
genai.configure(api_key="SUA_CHAVE_AQUI")
model = genai.GenerativeModel('gemini-pro')

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- FUNÇÕES COM IA ---
def gerar_pergunta_nivelamento(objetivo, nivel_teste):
    prompt = f"Gere uma frase em inglês de nível {nivel_teste} para o contexto de {objetivo}. A frase deve ser algo que alguém diria nessa situação. Retorne apenas a frase."
    response = model.generate_content(prompt)
    return response.text

def avaliar_resposta(pergunta, resposta_usuario, objetivo):
    prompt = f"O usuário ouviu a frase '{pergunta}' no contexto de {objetivo}. Ele respondeu: '{resposta_usuario}'. Com base na precisão da compreensão dele, qual o nível CEFR (A1, A2, B1, B2, C1) ele demonstra? Responda apenas a sigla do nível."
    response = model.generate_content(prompt)
    return response.text.strip()

# --- INTERFACE ---
st.title("🎤 LinguistAI Smart Coach")

if 'step' not in st.session_state:
    st.session_state.step = 'setup'

# PASSO 1: SETUP
if st.session_state.step == 'setup':
    st.header("Boas-vindas!")
    st.session_state.obj = st.selectbox("Qual seu foco?", ["Viagem", "Trabalho", "Acadêmico", "Social"])
    if st.button("Iniciar Teste de Nível Dinâmico"):
        with st.spinner("Gerando teste personalizado..."):
            st.session_state.pergunta_teste = gerar_pergunta_nivelamento(st.session_state.obj, "B1")
            st.session_state.step = 'test'
            st.rerun()

# PASSO 2: TESTE DINÂMICO
elif st.session_state.step == 'test':
    st.header("Teste de Nivelamento")
    st.write(f"Contexto: {st.session_state.obj}")
    
    if st.button("🔊 Ouvir Desafio"):
        play_audio(st.session_state.pergunta_teste)
    
    resp = st.text_input("O que você entendeu? (Resuma ou traduza)")
    
    if st.button("Finalizar Avaliação"):
        with st.spinner("A IA está avaliando sua fluência..."):
            nivel_final = avaliar_resposta(st.session_state.pergunta_teste, resp, st.session_state.obj)
            st.session_state.nivel = nivel_final
            st.session_state.step = 'dashboard'
            st.rerun()

# PASSO 3: DASHBOARD DE ESTUDOS
elif st.session_state.step == 'dashboard':
    st.balloons()
    st.header(f"Seu Nível: {st.session_state.nivel}")
    st.subheader(f"Plano de Estudos: {st.session_state.obj}")
    
    if st.button("Gerar Próxima Lição de Áudio"):
        # Aqui a IA geraria uma lição específica para o nível detectado
        prompt_licao = f"Gere um exercício curto de repetição para nível {st.session_state.nivel} sobre {st.session_state.obj}."
        aula = model.generate_content(prompt_licao)
        st.write(aula.text)
        
    if st.button("Refazer Teste"):
        st.session_state.step = 'setup'
        st.rerun()
        minha_chave = st.secrets["GOOGLE_API_KEY"]

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO INICIAL ---
# Substitua pela sua chave real ou use st.secrets para produção
API_KEY = "SUA_CHAVE_AQUI" 

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro ao configurar a IA. Verifique sua API Key.")

# --- FUNÇÕES AUXILIARES ---
def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except Exception as e:
        st.error("Erro ao gerar áudio. Verifique sua conexão.")

def chamar_ia(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return None

# --- GERENCIAMENTO DE ESTADO (MEMÓRIA) ---
if 'step' not in st.session_state:
    st.session_state.step = 'setup'
if 'nivel' not in st.session_state:
    st.session_state.nivel = 'A1'

# --- INTERFACE ---
st.set_page_config(page_title="LinguistAI", page_icon="🎤")

# Barra Lateral com Progresso
with st.sidebar:
    st.title("👤 Seu Perfil")
    if st.session_state.step != 'setup':
        st.write(f"**Objetivo:** {st.session_state.obj}")
        st.write(f"**Nível:** {st.session_state.nivel}")
    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- PASSO 1: SETUP ---
if st.session_state.step == 'setup':
    st.title("🚀 Bem-vindo ao LinguistAI")
    st.subheader("O app focado na sua fala e audição.")
    
    obj = st.selectbox("Qual seu objetivo final com o Inglês?", 
                        ["Trabalho (Business)", "Viagens (Travel)", "Acadêmico", "Social"])
    
    if st.button("Começar Teste de Nível"):
        st.session_state.obj = obj
        with st.spinner("A IA está preparando seu teste..."):
            prompt = f"Generate 1 short sentence in English for a B1 level student about {obj}. Return ONLY the sentence."
            frase = chamar_ia(prompt) or "I need to check my flight status at the counter."
            st.session_state.pergunta_teste = frase
            st.session_state.step = 'test'
            st.rerun()

# --- PASSO 2: TESTE DE NIVELAMENTO ---
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nivelamento")
    st.info(f"Contexto: {st.session_state.obj}")
    
    st.write("Clique no player abaixo para ouvir o desafio:")
    play_audio(st.session_state.pergunta_teste)
    
    resposta = st.text_input("O que você entendeu desta frase? (Escreva em Português ou Inglês)")
    
    if st.button("Finalizar Avaliação"):
        if resposta:
            with st.spinner("Avaliando..."):
                prompt_eval = f"User heard '{st.session_state.pergunta_teste}' and understood '{resposta}'. Based on Cambridge/CEFR, what is their level? Answer ONLY the level code (A1, A2, B1, B2, or C1)."
                result = chamar_ia(prompt_eval) or "B1"
                st.session_state.nivel = result
                st.session_state.step = 'practice'
                st.rerun()
        else:
            st.warning("Por favor, escreva o que entendeu antes de prosseguir.")

# --- PASSO 3: PRÁTICA INFINITA ---
elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    st.success(f"Nível Detectado: {st.session_state.nivel}")
    
    if st.button("✨ Gerar Nova Lição de Áudio"):
        with st.spinner("Criando exercício personalizado..."):
            prompt_aula = f"Generate an English learning exercise for level {st.session_state.nivel} about {st.session_state.obj}. Provide 1 phrase to repeat and its translation. Format: 'Phrase: [phrase] | Translation: [translation]'"
            aula = chamar_ia(prompt_aula)
            st.session_state.aula_atual = aula

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        st.write(st.session_state.aula_atual)
        try:
            frase_para_audio = st.session_state.aula_atual.split("Phrase:")[1].split("|")[0].strip()
            if st.button("🔊 Ouvir Frase"):
                play_audio(frase_para_audio)
        except:
            st.write("Use o botão acima para gerar uma lição.")
        minha_chave = st.secrets["GOOGLE_API_KEY"]

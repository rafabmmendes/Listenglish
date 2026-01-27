import streamlit as st
from gtts import gTTS
import base64
from io import BytesIO

# --- FUNÇÃO PARA GERAR ÁUDIO ---
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    audio_bytes = fp.getvalue()
    st.audio(audio_bytes, format="audio/mp3")

# --- INTERFACE ---
st.set_page_config(page_title="LinguistAI", page_icon="🎧")
st.title("🎧 LinguistAI: Teste Auditivo")

# Inicializa as variáveis de estado
if 'step' not in st.session_state:
    st.session_state.step = 'objective'
if 'level_passed' not in st.session_state:
    st.session_state.level_passed = False

# --- PASSO 1: OBJETIVO ---
if st.session_state.step == 'objective':
    st.subheader("Qual seu objetivo principal?")
    obj = st.selectbox("Escolha:", ["Business (Trabalho)", "Travel (Viagem)", "Social"])
    if st.button("Iniciar Teste"):
        st.session_state.objective = obj
        st.session_state.step = 'test_a2'
        st.rerun()

# --- PASSO 2: TESTE A2 ---
elif st.session_state.step == 'test_a2':
    st.header("Nível A2 - Básico")
    st.write("Ouça a frase e responda abaixo:")
    
    frase_a2 = "I am looking for the train station. Is it near here?"
    play_audio(frase_a2) # Agora o player fica fixo na tela
    
    resposta = st.text_input("O que a pessoa está procurando?", key="ans_a2")
    
    if st.button("Verificar Resposta"):
        if any(word in resposta.lower() for word in ["train", "trem", "estação", "station"]):
            st.success("Correto! Você está pronto para o próximo nível.")
            st.session_state.level_passed = True
        else:
            st.error("Incorreto. Tente ouvir novamente ou recomece.")

    if st.session_state.level_passed:
        if st.button("Avançar para Nível B2 ➡️"):
            st.session_state.level_passed = False
            st.session_state.step = 'test_b2'
            st.rerun()

# --- PASSO 3: TESTE B2 ---
elif st.session_state.step == 'test_b2':
    st.header("Nível B2 - Intermediário")
    st.write("Ouça com atenção o contexto profissional:")
    
    frase_b2 = "We need to schedule a meeting to discuss the budget cuts for the next quarter."
    play_audio(frase_b2)
    
    resposta_b2 = st.text_input("Qual o tema da reunião?", key="ans_b2")
    
    if st.button("Finalizar Teste"):
        if any(word in resposta_b2.lower() for word in ["budget", "orçamento", "cuts", "cortes"]):
            st.balloons()
            st.success(f"Excelente! Seu nível é B2/C1 em {st.session_state.objective}.")
        else:
            st.warning("Você chegou longe! Seu nível é B1.")
        
        if st.button("Recomeçar do Zero"):
            st.session_state.step = 'objective'
            st.session_state.level_passed = False
            st.rerun()
            

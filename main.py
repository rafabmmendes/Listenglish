import streamlit as st
from gtts import gTTS
import base64
from io import BytesIO

# --- FUNÇÃO PARA GERAR ÁUDIO ---
def speek(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp

def play_audio(text):
    audio_file = speek(text)
    audio_bytes = audio_file.getvalue()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_tag = f'<audio autoplay="true" src="data:audio/wav;base64,{audio_base64}">'
    st.markdown(audio_tag, unsafe_allow_html=True)

# --- INTERFACE DO APP ---
st.set_page_config(page_title="LinguistAI - Audio Focus", page_icon="🎧")
st.title("🎧 LinguistAI: Teste Auditivo")

if 'step' not in st.session_state:
    st.session_state.step = 'objective'

# PASSO 1: OBJETIVO
if st.session_state.step == 'objective':
    st.subheader("Qual seu objetivo principal?")
    obj = st.selectbox("Escolha:", ["Business (Trabalho)", "Travel (Viagem)", "Social"])
    if st.button("Iniciar Teste de Nivelamento"):
        st.session_state.objective = obj
        st.session_state.step = 'test_a2'
        st.rerun()

# PASSO 2: TESTE A2 (BÁSICO)
elif st.session_state.step == 'test_a2':
    st.header("Nível A2 - Ouça com atenção")
    
    frase_a2 = "Hello! I am looking for the train station. Is it near here?"
    
    if st.button("🔊 Ouvir Áudio"):
        play_audio(frase_a2)
    
    resposta = st.text_input("O que a pessoa está procurando?")
    
    if st.button("Verificar"):
        if "train" in resposta.lower() or "trem" in resposta.lower() or "estação" in resposta.lower():
            st.success("Muito bem! Você captou a palavra-chave.")
            if st.button("Ir para o Nível B2"):
                st.session_state.step = 'test_b2'
                st.rerun()
        else:
            st.error("Não foi dessa vez. Seu nível atual é A1/A2.")
            if st.button("Recomeçar"):
                st.session_state.step = 'objective'
                st.rerun()

# PASSO 3: TESTE B2 (INTERMEDIÁRIO)
elif st.session_state.step == 'test_b2':
    st.header("Nível B2 - Contexto Profissional")
    
    frase_b2 = "We need to schedule a meeting to discuss the budget cuts for the next quarter."
    
    if st.button("🔊 Ouvir Áudio"):
        play_audio(frase_b2)
        
    resposta_b2 = st.text_input("Sobre o que será a reunião?")
    
    if st.button("Finalizar Teste"):
        if "budget" in resposta_b2.lower() or "orçamento" in resposta_b2.lower():
            st.balloons()
            st.success("Incrível! Você tem uma ótima compreensão auditiva (Nível B2/C1).")
        else:
            st.warning("Você entendeu parte, mas seu nível é B1.")
        
        if st.button("Voltar ao Início"):
            st.session_state.step = 'objective'
            st.rerun()

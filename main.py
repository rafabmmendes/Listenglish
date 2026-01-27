import streamlit as st
from gtts import gTTS
from io import BytesIO
import google.generativeai as genai # Biblioteca da IA

# --- CONFIGURAÇÃO DA IA ---
# Você consegue sua chave em: https://aistudio.google.com/
genai.configure(api_key="SUA_CHAVE_AQUI")
model = genai.GenerativeModel('gemini-pro')

def gerar_licao_ia(objetivo, nivel):
    prompt = f"""
    Gere uma lição de inglês para o objetivo {objetivo} no nível {nivel} de Cambridge.
    Retorne apenas no formato:
    Frase em Inglês: [frase]
    Tradução: [tradução]
    Instrução: [instrução de o que fazer]
    """
    response = model.generate_content(prompt)
    return response.text

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- INTERFACE ---
st.title("🤖 LinguistAI: Lições Infinitas com IA")

if 'licao_atual' not in st.session_state:
    st.session_state.licao_atual = None

# Seleção de Nível e Objetivo
col1, col2 = st.columns(2)
with col1:
    obj = st.selectbox("Foco:", ["Marketing", "Medicina", "TI", "Viagem", "Vendas"])
with col2:
    nivel = st.selectbox("Nível:", ["A2", "B1", "B2", "C1"])

if st.button("Gerar Nova Lição Personalizada ✨"):
    with st.spinner('A IA está criando sua lição...'):
        st.session_state.licao_atual = gerar_licao_ia(obj, nivel)

# Exibição da Lição Gerada pela IA
if st.session_state.licao_atual:
    st.markdown("---")
    st.write(st.session_state.licao_atual)
    
    # Extrair a frase em inglês para o áudio (lógica simples de busca de texto)
    try:
        frase_en = st.session_state.licao_atual.split("Frase em Inglês:")[1].split("\n")[0]
        if st.button("🔊 Ouvir Pronúncia da IA"):
            play_audio(frase_en)
    except:
        st.write("Erro ao processar áudio. Tente gerar outra lição.")

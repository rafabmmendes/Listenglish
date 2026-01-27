import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO ---
API_KEY = "SUA_CHAVE_AQUI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- ESTADO DO JOGO ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'

# --- INTERFACE ---
st.set_page_config(page_title="LinguistAI", page_icon="🎤")

with st.sidebar:
    st.title("👤 Seu Perfil")
    if 'obj' in st.session_state:
        st.metric(label="Nível Atual", value=st.session_state.nivel)
        st.write(f"**Foco:** {st.session_state.obj}")
        
        # Barra de XP
        st.write(f"**XP Total:** {st.session_state.xp}")
        progresso = min(st.session_state.xp / 100, 1.0) # Nível sobe a cada 100 XP
        st.progress(progresso)
        st.caption(f"{st.session_state.xp}/100 para o próximo bônus")

    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- LÓGICA DE TELAS ---
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Selecione seu objetivo:", ["Trabalho (Business)", "Viagens (Travel)", "Social"])
    if st.button("Iniciar"):
        st.session_state.obj = obj
        # Simulação rápida de nivelamento para o código não ficar gigante
        st.session_state.step = 'practice' 
        st.rerun()

elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    
    if st.button("✨ Gerar Nova Lição de Áudio"):
        with st.spinner("IA criando lição..."):
            prompt = f"Crie uma frase curta em inglês nível {st.session_state.nivel} sobre {st.session_state.obj}. Formato: Frase: [frase] | Tradução: [tradução]"
            res = model.generate_content(prompt).text
            st.session_state.aula_atual = res
            # Ganha XP ao gerar
            st.session_state.xp += 10

    if 'aula_atual' in st.session_state and st.session_state.aula_atual:
        st.markdown("---")
        partes = st.session_state.aula_atual.split("|")
        frase_en = partes[0].replace("Frase:", "").strip()
        traducao = partes[1].replace("Tradução:", "").strip()
        
        st.subheader("Traduza Mentalmente:")
        st.info(traducao)
        
        if st.button("🔊 Ouvir Resposta em Inglês"):
            play_audio(frase_en)
            st.success(f"A frase era: {frase_en}")
            st.toast("XP Ganho! +10", icon="🔥")
        minha_chave = st.secrets["GOOGLE_API_KEY"]

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO DA IA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Tentativa com o nome de modelo mais simples possível
        # O SDK cuida de encontrar a versão correta (v1 ou v1beta)
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("Chave 'GOOGLE_API_KEY' não encontrada nos Secrets.")
except Exception as e:
    st.error(f"Erro de configuração: {e}")

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Erro ao gerar áudio.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    if 'obj' in st.session_state:
        st.write(f"**Foco:** {st.session_state.obj}")
        st.write(f"**XP:** {st.session_state.xp}")
    if st.button("Reiniciar Aplicativo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---
if st.session_state.step == 'setup':
    st.title("🎧 LinguistAI")
    obj = st.selectbox("Seu foco:", ["Business", "Travel", "Social"])
    if st.button("Começar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("IA criando lição..."):
            try:
                prompt = f"Create 1 short English sentence for {st.session_state.obj}. Format: Phrase: [English] | Translation: [Portuguese]"
                # Forçamos a geração sem parâmetros extras para evitar erros de versão
                response = model.generate_content(prompt)
                
                if response:
                    st.session_state.aula_atual = response.text
                    st.session_state.xp += 10
            except Exception as e:
                st.error(f"Erro ao chamar a IA: {e}")
                st.info("Dica: Verifique se sua API Key no Google AI Studio tem acesso ao modelo Gemini 1.5 Flash.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        texto = st.session_state.aula_atual
        if "|" in texto:
            try:
                partes = texto.split("|")
                ingles = partes[0].replace("Phrase:", "").strip()
                portugues = partes[1].replace("Translation:", "").strip()
                st.subheader("Como se diz:")
                st.info(portugues)
                if st.button("🔊 Ouvir em Inglês"):
                    play_audio(ingles)
                    st.success(f"Inglês: {ingles}")
            except:
                st.write(texto)
        else:
            st.write(texto)

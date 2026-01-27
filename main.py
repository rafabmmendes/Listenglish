import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO DA IA ---
@st.cache_resource
def configurar_modelo():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            # Lista os modelos para encontrar um que suporte geração de conteúdo
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Prioriza o flash, mas aceita o que estiver disponível
                    if 'gemini-1.5-flash' in m.name or 'gemini-pro' in m.name:
                        return genai.GenerativeModel(m.name)
        return None
    except Exception as e:
        st.error(f"Erro ao listar modelos: {e}")
        return None

model = configurar_modelo()

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
    if model:
        st.success("Conectado à IA ✅")
    else:
        st.error("IA Desconectada ❌")
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
        if not model:
            st.error("Modelo não configurado. Verifique sua API Key nos Secrets.")
        else:
            with st.spinner("IA criando lição..."):
                try:
                    prompt = f"Create 1 short English sentence for {st.session_state.obj}. Format: Phrase: [English] | Translation: [Portuguese]"
                    response = model.generate_content(prompt)
                    st.session_state.aula_atual = response.text
                    st.session_state.xp += 10
                except Exception as e:
                    st.error(f"Erro na geração: {e}")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        texto = st.session_state.aula_atual
        if "|" in texto:
            partes = texto.split("|")
            ingles = partes[0].replace("Phrase:", "").strip()
            portugues = partes[1].replace("Translation:", "").strip()
            st.subheader("Tradução:")
            st.info(portugues)
            if st.button("🔊 Ouvir em Inglês"):
                play_audio(ingles)
                st.write(f"✅ **Inglês:** {ingles}")

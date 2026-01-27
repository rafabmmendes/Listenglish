import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO ---
# Se estiver no Streamlit Cloud, o ideal é usar st.secrets["GOOGLE_API_KEY"]
API_KEY = "SUA_CHAVE_AQUI" 

try:
    genai.configure(api_key=API_KEY)
    # Configuração para ignorar bloqueios de segurança bobos em frases de estudo
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 200,
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config
    )
except Exception as e:
    st.error(f"Erro de Configuração: {e}")

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("⚠️ O player de áudio falhou. Tente novamente.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'nivel' not in st.session_state: st.session_state.nivel = 'B1'

# --- INTERFACE ---
st.set_page_config(page_title="LinguistAI", page_icon="🎤")

with st.sidebar:
    st.title("👤 Perfil")
    if 'obj' in st.session_state:
        st.write(f"**Nível:** {st.session_state.nivel}")
        st.write(f"**XP:** {st.session_state.xp}")
        st.progress(min(st.session_state.xp / 100, 1.0))
    if st.button("Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---
if st.session_state.step == 'setup':
    st.title("🚀 Configuração")
    obj = st.selectbox("Seu foco:", ["Business", "Travel", "Social"])
    if st.button("Confirmar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

elif st.session_state.step == 'practice':
    st.title("🏋️ Prática")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("IA criando lição..."):
            # Prompt mais explícito para evitar erros de interpretação da API
            prompt = f"Create a short English learning task for {st.session_state.obj} objective. Level {st.session_state.nivel}. Format exactly like this: Phrase: [English Sentence] | Translation: [Portuguese Translation]"
            
            try:
                response = model.generate_content(prompt)
                # Verifica se a resposta foi bloqueada por segurança
                if response.candidates:
                    st.session_state.aula_atual = response.text
                    st.session_state.xp += 10
                else:
                    st.error("A IA recusou gerar esse conteúdo. Tente novamente.")
            except Exception as e:
                st.error(f"Erro na chamada da IA: {e}")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        try:
            # Separando com segurança
            raw_text = st.session_state.aula_atual
            if "|" in raw_text:
                partes = raw_text.split("|")
                frase_en = partes[0].replace("Phrase:", "").strip()
                traducao = partes[1].replace("Translation:", "").strip()
                
                st.subheader("Tradução:")
                st.info(traducao)
                
                if st.button("🔊 Ouvir Pronúncia"):
                    play_audio(frase_en)
                    st.write(f"**Inglês:** {frase_en}")
            else:
                st.write(raw_text) # Mostra o texto bruto se o split falhar
        except Exception as e:
            st.write("Houve um erro ao processar o texto da lição.")
        minha_chave = st.secrets["GOOGLE_API_KEY"]

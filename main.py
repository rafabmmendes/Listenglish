import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO DE SEGURANÇA (ST.SECRETS) ---
# O código vai procurar uma chave chamada 'GOOGLE_API_KEY' nas configurações do Streamlit
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        # Caso você ainda esteja testando localmente, ele tenta pegar o valor manual abaixo
        # Mas o ideal é colocar no painel 'Secrets' do Streamlit Cloud
        API_KEY_MANUAL = "COLE_SUA_CHAVE_AQUI_SE_NAO_USAR_SECRETS"
        genai.configure(api_key=API_KEY_MANUAL)

    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro de conexão: Verifique se a API Key foi inserida corretamente nos Secrets.")

# --- FUNÇÕES AUXILIARES ---
def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Falha ao gerar áudio. Tente gerar uma nova lição.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'nivel' not in st.session_state: st.session_state.nivel = 'B1'

# --- INTERFACE ---
st.set_page_config(page_title="LinguistAI", page_icon="🎤")

with st.sidebar:
    st.title("👤 Seu Perfil")
    if 'obj' in st.session_state:
        st.metric(label="Nível", value=st.session_state.nivel)
        st.write(f"**XP:** {st.session_state.xp}")
        st.progress(min(st.session_state.xp / 100, 1.0))
    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Qual seu foco?", ["Business (Trabalho)", "Travel (Viagem)", "Social"])
    if st.button("Confirmar e Começar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

elif st.session_state.step == 'practice':
    st.title("🏋️ Prática Diária")
    
    if st.button("✨ Gerar Nova Lição de Áudio"):
        with st.spinner("IA criando lição personalizada..."):
            prompt = (f"Create a short English learning task for {st.session_state.obj}. "
                      f"Level {st.session_state.nivel}. "
                      f"Format: Phrase: [English Sentence] | Translation: [Portuguese Translation]")
            try:
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except Exception as e:
                st.error(f"Erro na IA: {e}")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        try:
            raw_text = st.session_state.aula_atual
            if "|" in raw_text:
                partes = raw_text.split("|")
                frase_en = partes[0].replace("Phrase:", "").strip()
                traducao = partes[1].replace("Translation:", "").strip()
                
                st.subheader("Tradução (O que você deve dizer/entender):")
                st.info(traducao)
                
                if st.button("🔊 Ouvir Resposta em Inglês"):
                    play_audio(frase_en)
                    st.write(f"**Inglês:** {frase_en}")
                    st.toast("+10 XP!", icon="🔥")
            else:
                st.write(raw_text)
        except:
            st.error("Erro ao formatar a lição. Tente gerar outra.")

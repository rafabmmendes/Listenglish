import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder # Nova biblioteca

# --- CONFIGURAÇÃO ---
@st.cache_resource
def load_model():
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = load_model()

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- INICIALIZAÇÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    if st.button("🔄 Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🗣️ Treino de Fala (Speaking)")

if st.button("✨ Nova Frase para Praticar"):
    with st.spinner("IA criando frase..."):
        try:
            seed = random.randint(1, 10000)
            prompt = f"Level {st.session_state.nivel} English sentence. Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
            res = model.generate_content(prompt)
            st.session_state.aula_atual = res.text
            st.session_state.feedback = None
        except:
            st.error("Erro na IA. Aguarde 15 segundos.")

if st.session_state.aula_atual:
    st.markdown("---")
    texto = st.session_state.aula_atual
    ingles_correto = texto.split("|")[0].split(":")[-1].strip()
    portugues = texto.split("|")[1].split(":")[-1].strip()
    
    st.subheader("Como se diz em inglês?")
    st.info(f"💡 {portugues}")
    
    if st.button("🔊 Ouvir Pronúncia Original"):
        play_audio(ingles_correto)

    st.write("### 🎤 Grave sua voz falando a frase:")
    
    # COMPONENTE DE GRAVAÇÃO
    audio_gravado = mic_recorder(
        start_prompt="Clique para Gravar",
        stop_prompt="Parar Gravação",
        key='recorder'
    )

    if audio_gravado:
        st.audio(audio_gravado['bytes']) # Toca sua própria voz de volta
        
        if st.button("🔍 Analisar minha pronúncia"):
            with st.spinner("IA analisando seu áudio..."):
                try:
                    # Usamos a capacidade multimodal do Gemini para ouvir o áudio
                    # ou enviamos os bytes para transcrição
                    audio_data = {
                        "mime_type": "audio/wav",
                        "data": audio_gravado['bytes']
                    }
                    
                    prompt_analise = (
                        f"O aluno deveria falar: '{ingles_correto}'. "
                        f"Ouça o áudio anexo e diga se a pronúncia está correta. "
                        f"Dê dicas curtas em português sobre como melhorar."
                    )
                    
                    # O Gemini 1.5 Flash aceita áudio diretamente!
                    response = model.generate_content([prompt_analise, audio_data])
                    st.session_state.feedback = response.text
                    
                    if "parabéns" in response.text.lower() or "correto" in response.text.lower():
                        st.session_state.xp += 25
                        st.balloons()
                except Exception as e:
                    st.error("A IA não conseguiu processar o áudio agora. Tente novamente.")

    if 'feedback' in st.session_state and st.session_state.feedback:
        st.subheader("Análise da IA:")
        st.write(st.session_state.feedback)
        st.write(f"**Gabarito:** {ingles_correto}")

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

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

# --- BANCO DE DADOS DE RESERVA ---
FRASES_RESERVA = [
    {"en": "I am looking for the airport.", "pt": "Estou procurando o aeroporto."},
    {"en": "The meeting starts at nine.", "pt": "A reunião começa às nove."},
    {"en": "This is a very important step.", "pt": "Este é um passo muito importante."}
]

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- INICIALIZAÇÃO DO ESTADO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'erros_foneticos' not in st.session_state: 
    st.session_state.erros_foneticos = {"Vogais": 0, "Consoantes (TH/R)": 0, "Entonação": 0}
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'feedback' not in st.session_state: st.session_state.feedback = ""

# --- SIDEBAR COM DASHBOARD ---
with st.sidebar:
    st.title("📊 Seu Desempenho")
    st.metric("Nível CEFR", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    
    st.write("---")
    st.subheader("Foco de Melhoria:")
    # Exibe um mini gráfico de barras para os erros
    for categoria, valor in st.session_state.erros_foneticos.items():
        st.write(f"{categoria}: {valor}")
        st.progress(min(valor / 10, 1.0))
    
    if st.button("🔄 Reiniciar Tudo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA DE TREINO ---
st.title("🗣️ Trainer de Conversação")

if st.button("✨ Gerar Nova Lição"):
    try:
        seed = random.randint(1, 10000)
        prompt = f"English level {st.session_state.nivel}. Phrase: [English] | Translation: [Portuguese]. Seed: {seed}"
        res = model.generate_content(prompt)
        st.session_state.aula_atual = res.text
        st.session_state.feedback = ""
    except:
        item = random.choice(FRASES_RESERVA)
        st.session_state.aula_atual = f"Phrase: {item['en']} | Translation: {item['pt']}"
        st.info("Usando lição de reserva para poupar sua cota de IA.")

if st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ing = texto.split("|")[0].split(":")[-1].strip()
        pt = texto.split("|")[1].split(":")[-1].strip()
        
        st.info(f"**Traduza e fale:** {pt}")
        if st.button("🔊 Ouvir Referência"):
            play_audio(ing)

        st.write("### 🎤 Grave sua pronúncia:")
        audio_gravado = mic_recorder(start_prompt="Gravar", stop_prompt="Parar", key='recorder_fala')

        if audio_gravado:
            if st.button("🔍 Analisar Fala"):
                with st.spinner("Analisando fonemas..."):
                    try:
                        audio_data = {"mime_type": "audio/wav", "data": audio_gravado['bytes']}
                        prompt_analise = (
                            f"Student said this for: '{ing}'. Analyze pronunciation. "
                            f"Identify if errors are in 'Vogais', 'Consoantes' or 'Entonação'. "
                            f"Give feedback in Portuguese. If correct, say 'PARABÉNS'."
                        )
                        response = model.generate_content([prompt_analise, audio_data])
                        st.session_state.feedback = response.text
                        
                        # Simulação de contagem de erros para o gráfico
                        if "vogal" in response.text.lower(): st.session_state.erros_foneticos["Vogais"] += 1
                        if "consoante" in response.text.lower() or "th" in response.text.lower(): 
                            st.session_state.erros_foneticos["Consoantes (TH/R)"] += 1
                        
                        st.session_state.xp += 20
                    except:
                        st.error("IA ocupada. Tente analisar novamente em 15s.")

        if st.session_state.feedback:
            st.success("Análise Detalhada:")
            st.write(st.session_state.feedback)
            st.write(f"✅ **Gabarito:** {ing}")
    except:
        st.error("Erro ao carregar frase.")

# Evolução Automática
niveis = ["A1", "A2", "B1", "B2", "C1"]
if st.session_state.xp >= 100:
    idx = niveis.index(st.session_state.nivel)
    if idx < len(niveis)-1:
        st.session_state.nivel = niveis[idx+1]
        st.session_state.xp = 0
        st.balloons()

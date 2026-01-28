import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro: API Key não configurada.")

DIFICULDADES = [
    {"nivel": "Begginer", "desc": "Short phrases, simple greetings."},
    {"nivel": "Basic", "desc": "Sentences in present tense about daily life."},
    {"nivel": "Intermediate", "desc": "Past and future tenses with connectors."},
    {"nivel": "Advanced", "desc": "Complex sentences with phrasal verbs."},
    {"nivel": "Professional", "desc": "Business English and workplace scenarios."},
    {"nivel": "Fluenty", "desc": "Native-level slang and idioms."}
]

# --- 2. FUNÇÃO DE ÁUDIO (FOCO NA PRONÚNCIA PT) ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        
        # ID Único para garantir que o áudio mude sempre
        unique_id = f"aud_{time.time()}_{random.randint(1, 1000)}"
        
        # Estilo diferente para o áudio em Português
        bg_color = "#2e7d32" if lang == 'pt' else "#1e1e1e"
        border_color = "#4caf50" if lang == 'pt' else "#444"
        
        md = f"""
            <div style="margin: 15px 0; padding: 15px; border: 2px solid {border_color}; border-radius: 15px; background-color: {bg_color}; color: white;">
                <strong style="font-size: 1.1em;">🔊 {label}</strong><br>
                <audio id="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%; margin-top: 10px;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Erro ao gerar áudio.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel_idx' not in st.session_state: st.session_state.nivel_idx = 0
if 'modo' not in st.session_state: st.session_state.modo = 'Prática'
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'audio_key' not in st.session_state: st.session_state.audio_key = 0
if 'audio_inicial_ok' not in st.session_state: st.session_state.audio_inicial_ok = False

nivel_atual = DIFICULDADES[st.session_state.nivel_idx]["nivel"]

# --- 4. FUNÇÃO PARA GERAR NOVA PERGUNTA ---
def proxima_pergunta():
    st.session_state.frase_en = None
    st.session_state.frase_pt = None
    st.session_state.feedback = None
    st.session_state.audio_inicial_ok = False
    st.session_state.audio_key += 1
    
    prompt = (f"Level: {nivel_atual}. Generate a UNIQUE sentence. "
              f"Format: Phrase: [English] | Translation: [Portuguese]")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0
        ).choices[0].message.content
        
        if "|" in res:
            st.session_state.frase_en = res.split("|")[0].split("Phrase:")[-1].strip(" []")
            st.session_state.frase_pt = res.split("|")[1].split("Translation:")[-1].strip(" []")
    except:
        st.error("Erro na IA. Tente novamente.")

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🏆 Maestria")
    st.session_state.modo = st.radio("Modo:", ["Prática", "Teste de Maestria"])
    st.divider()
    st.write(f"📈 Nível: **{nivel_atual}**")
    if st.session_state.modo == "Teste de Maestria":
        st.write(f"Streak: {st.session_state.test_streak}/5")
        st.progress(st.session_state.test_streak / 5)

st.title("🎙️ Gemini English Coach")

if st.button("⏭️ PRÓXIMA FRASE", type="primary") or st.session_state.frase_pt is None:
    proxima_pergunta()
    st.rerun()

# --- EXIBIÇÃO DA PRONÚNCIA ---
if st.session_state.frase_pt:
    st.info(f"### Traduza: {st.session_state.frase_pt}")

    # AQUI ESTÁ A PRONÚNCIA EM PORTUGUÊS (PLAYER VERDE)
    if not st.session_state.audio_inicial_ok:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=True, label="PRONÚNCIA EM PORTUGUÊS")
        st.session_state.audio_inicial_ok = True
    else:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=False, label="REPETIR PORTUGUÊS")

    st.divider()

    # MICROFONE
    audio_data = mic_recorder(start_prompt="🎤 Gravar Inglês", stop_prompt="⏹️ Parar", key=f"mic_{st.session_state.audio_key}")

    if audio_data:
        # (Lógica de transcrição e feedback igual às versões anteriores...)
        with st.spinner("Analisando..."):
            transcript = client.audio.transcriptions.create(file=("audio.wav", audio_data['bytes']), model="whisper-large-v3-turbo", response_format="text")
            f_prompt = f"Student said '{transcript}' for '{st.session_state.frase_en}'. Correct? Start with CORRETO."
            eval_text = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f_prompt}]).choices[0].message.content
            st.session_state.feedback = {"falado": transcript, "texto": eval_text}

    if st.session_state.feedback:
        st.write(f"📝 {st.session_state.feedback['texto']}")
        st.success(f"✅ Gabarito: {st.session_state.frase_en}")
        play_audio(st.session_state.frase_en, lang='en', label="PRONÚNCIA EM INGLÊS")
        
        # Lógica de subir nível (5 acertos)
        if "CORRETO" in st.session_state.feedback['texto'].upper() and st.session_state.modo == "Teste de Maestria":
            st.session_state.test_streak += 1
            if st.session_state.test_streak >= 5:
                st.balloons()
                if st.session_state.nivel_idx < len(DIFICULDADES) - 1:
                    st.session_state.nivel_idx += 1
                    st.session_state.test_streak = 0
        elif st.session_state.modo == "Teste de Maestria":
            st.session_state.test_streak = 0

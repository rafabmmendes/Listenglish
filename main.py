import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key.")

DIFICULDADES = {
    "Begginer": "Super simple greetings and 2-word sentences.",
    "basic": "Daily routines and simple present.",
    "intermediate": "Past/Future and connectors like 'because'.",
    "advanced": "Native idioms and phrasal verbs.",
    "professional": "Corporate formal English.",
    "fluenty": "Slang and complex metaphors."
}

# --- 2. FUNÇÃO DE ÁUDIO ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f"""
            <div style="margin: 10px 0;">
                <small>{label}</small><br>
                <audio controls {"autoplay" if autoplay else ""} style="width: 100%; height: 40px;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except: st.warning("Erro áudio.")

# --- 3. ESTADO DA SESSÃO (INICIALIZAÇÃO) ---
if 'frase_pt' not in st.session_state: st.session_state.frase_pt = None
if 'frase_en' not in st.session_state: st.session_state.frase_en = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'audio_tocado' not in st.session_state: st.session_state.audio_tocado = False
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0

# --- 4. LÓGICA DE GERAÇÃO (O segredo da mudança) ---
def buscar_nova_pergunta():
    # 1. Limpa tudo o que existe para não mostrar a velha
    st.session_state.frase_pt = None
    st.session_state.frase_en = None
    st.session_state.feedback = None
    st.session_state.audio_tocado = False
    st.session_state.mic_key += 1 # Reseta o gravador
    
    # 2. Gera um ID único para enganar o cache da API
    token_unico = f"{time.time()}-{random.randint(1, 9999)}"
    
    prompt = (f"ID: {token_unico}. Nível: {st.session_state.get('nivel_sel', 'Begginer')}. "
              f"Instrução: {DIFICULDADES.get(st.session_state.get('nivel_sel', 'Begginer'))}. "
              f"Gere uma frase COMPLETAMENTE NOVA. Varie os temas. "
              f"Formato: Phrase: [Inglês] | Translation: [Português]")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0 # Criatividade no máximo
        ).choices[0].message.content
        
        if "|" in res:
            st.session_state.frase_en = res.split("|")[0].split("Phrase:")[-1].strip(" []")
            st.session_state.frase_pt = res.split("|")[1].split("Translation:")[-1].strip(" []")
    except:
        st.error("Erro na API.")

# --- 5. INTERFACE ---
st.title("🗣️ Treino Oral de Inglês")

with st.sidebar:
    st.session_state.nivel_sel = st.selectbox("Nível:", list(DIFICULDADES.keys()))
    if st.button("♻️ Resetar Tudo"):
        st.session_state.clear()
        st.rerun()

# Botão que força a mudança
if st.button("⏭️ PRÓXIMA PERGUNTA", type="primary"):
    buscar_nova_pergunta()
    st.rerun()

# Se estiver vazio (primeira vez), busca
if st.session_state.frase_pt is None:
    buscar_nova_pergunta()

# EXIBIÇÃO
if st.session_state.frase_pt:
    st.info(f"### Traduza: {st.session_state.frase_pt}")
    
    # Áudio Automático PT
    if not st.session_state.audio_tocado:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=True, label="Ouvir Desafio (PT)")
        st.session_state.audio_tocado = True
    else:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=False, label="Repetir (PT)")

    st.divider()

    # GRAVAÇÃO
    audio = mic_recorder(start_prompt="🎤 Gravar Resposta", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

    if audio:
        with st.spinner("Analisando..."):
            transcript = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3-turbo", response_format="text")
            
            f_prompt = f"O aluno disse '{transcript}' para '{st.session_state.frase_en}'. Corrija. Se estiver certo diga CORRETO."
            feedback_ia = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f_prompt}]).choices[0].message.content
            
            st.session_state.feedback = {"falado": transcript, "texto": feedback_ia}

    if st.session_state.feedback:
        st.success(f"✅ **Gabarito:** {st.session_state.frase_en}")
        play_audio(st.session_state.frase_en, lang='en', label="Pronúncia Correta (EN)")
        st.write(f"🗣️ **Você disse:** {st.session_state.feedback['falado']}")
        st.write(f"📝 **Análise:** {st.session_state.feedback['texto']}")

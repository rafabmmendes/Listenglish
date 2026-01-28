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
    "Begginer": "Short phrases, simple greetings.",
    "basic": "Daily routines, simple present.",
    "intermediate": "Past/Future events and connectors.",
    "advanced": "Complex idioms and phrasal verbs.",
    "professional": "Workplace scenarios and formal terms.",
    "fluenty": "Slang, metaphors, and native nuances."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f"""
            <div style="margin: 10px 0;">
                <small>{label} ({lang.upper()})</small><br>
                <audio controls {"autoplay" if autoplay else ""} style="width: 100%; height: 40px;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Erro ao gerar áudio.")

# --- 3. ESTADO DA SESSÃO ---
# Inicializamos variáveis essenciais para não dar erro de "não definido"
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'pergunta_pt' not in st.session_state: st.session_state.pergunta_pt = None
if 'pergunta_en' not in st.session_state: st.session_state.pergunta_en = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'audio_inicial_tocado' not in st.session_state: st.session_state.audio_inicial_tocado = False
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0

# --- 4. FUNÇÃO PARA GERAR NOVA FRASE ---
def gerar_nova_frase():
    # Esta função força a IA a criar algo novo usando um timestamp único
    seed = f"{time.time()}-{random.randint(100, 999)}"
    prompt = (f"Seed: {seed}. Nível: {st.session_state.nivel}. "
              f"Instrução: {DIFICULDADES[st.session_state.nivel]}. "
              f"Gere uma frase ÚNICA. Formato: Phrase: [Inglês] | Translation: [Português]")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0 # Criatividade máxima
        ).choices[0].message.content
        
        if "|" in res:
            st.session_state.pergunta_en = res.split("|")[0].split("Phrase:")[-1].strip(" []")
            st.session_state.pergunta_pt = res.split("|")[1].split("Translation:")[-1].strip(" []")
            st.session_state.feedback = None
            st.session_state.audio_inicial_tocado = False
            st.session_state.mic_key += 1
    except:
        st.error("Erro ao conectar com a IA.")

# --- 5. INTERFACE ---

st.title("🗣️ Treino de Inglês Dinâmico")

# Sidebar
with st.sidebar:
    st.session_state.nivel = st.selectbox("Nível:", LISTA_NIVEIS)
    st.session_state.modo = st.radio("Modo:", ["Prática", "Teste"])
    if st.button("♻️ Reiniciar App"):
        st.session_state.clear()
        st.rerun()

# Botão principal de troca
if st.button("⏭️ PRÓXIMA PERGUNTA", type="primary"):
    gerar_nova_frase()

# Se não houver pergunta, gera a primeira
if st.session_state.pergunta_pt is None:
    gerar_nova_frase()

# EXIBIÇÃO DA TAREFA
if st.session_state.pergunta_pt:
    st.write("---")
    st.subheader("Traduza para o Inglês:")
    st.info(f"### {st.session_state.pergunta_pt}")

    # ÁUDIO AUTOMÁTICO EM PORTUGUÊS
    if not st.session_state.audio_inicial_tocado:
        play_audio(st.session_state.pergunta_pt, lang='pt', autoplay=True, label="Ouvir Desafio")
        st.session_state.audio_inicial_tocado = True
    else:
        play_audio(st.session_state.pergunta_pt, lang='pt', autoplay=False, label="Repetir Desafio")

    st.write("---")
    
    # GRAVADOR
    audio = mic_recorder(
        start_prompt="🎤 Gravar sua Tradução", 
        stop_prompt="⏹️ Analisar", 
        key=f"mic_{st.session_state.mic_key}"
    )

    if audio:
        with st.spinner("IA Analisando..."):
            # Transcrição
            transcript = client.audio.transcriptions.create(
                file=("audio.wav", audio['bytes']), 
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
            
            # Comparação
            f_prompt = f"O aluno disse '{transcript}' para '{st.session_state.pergunta_en}'. Corrija em PT-BR. Se estiver 100% certo, use a palavra CORRETO."
            feedback = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f_prompt}]
            ).choices[0].message.content
            
            st.session_state.feedback = {
                "falado": transcript,
                "texto": feedback
            }

    # RESULTADOS (SÓ APARECEM APÓS O FEEDBACK)
    if st.session_state.feedback:
        st.divider()
        st.success(f"✅ **Gabarito:** {st.session_state.pergunta_en}")
        play_audio(st.session_state.pergunta_en, lang='en', autoplay=False, label="Ouvir Pronúncia Correta")
        
        st.write(f"🗣️ **Você disse:** {st.session_state.feedback['falado']}")
        st.write(f"📝 **Feedback:** {st.session_state.feedback['texto']}")

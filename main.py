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
    st.error("Erro: API Key não configurada nos Secrets do Streamlit.")

DIFICULDADES = [
    {"nivel": "Begginer", "desc": "Short phrases, simple greetings."},
    {"nivel": "Basic", "desc": "Sentences in present tense about daily life."},
    {"nivel": "Intermediate", "desc": "Past and future tenses with connectors."},
    {"nivel": "Advanced", "desc": "Complex sentences with phrasal verbs."},
    {"nivel": "Professional", "desc": "Business English and workplace scenarios."},
    {"nivel": "Fluenty", "desc": "Native-level slang and idioms."}
]

# --- 2. FUNÇÃO DE ÁUDIO (COM QUEBRA DE CACHE) ---
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        # unique_id evita que o navegador toque o áudio antigo da memória
        unique_id = f"{time.time()}_{random.randint(1, 1000)}"
        md = f"""
            <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 10px; background-color: #1e1e1e; color: white;">
                <small>{label}</small><br>
                <audio id="{unique_id}" controls {"autoplay" if autoplay else ""} style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}#t={unique_id}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Áudio indisponível momentaneamente.")

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
desc_atual = DIFICULDADES[st.session_state.nivel_idx]["desc"]

# --- 4. FUNÇÃO PARA GERAR NOVA PERGUNTA ---
def proxima_pergunta():
    st.session_state.frase_en = None
    st.session_state.frase_pt = None
    st.session_state.feedback = None
    st.session_state.audio_inicial_ok = False
    st.session_state.audio_key += 1
    
    seed = f"{time.time()}-{random.randint(1, 9999)}"
    prompt = (f"Seed: {seed}. Level: {nivel_atual}. Context: {desc_atual}. "
              f"Generate a UNIQUE sentence. Format: Phrase: [English] | Translation: [Portuguese]")
    
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
        st.error("Falha ao gerar frase. Tente novamente.")

# --- 5. INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.title("🏆 Maestria")
    st.session_state.modo = st.radio("Modo de Jogo:", ["Prática", "Teste de Maestria"])
    st.divider()
    st.write(f"📈 Nível Atual: **{nivel_atual}**")
    
    if st.session_state.modo == "Teste de Maestria":
        st.write(f"Sequência: **{st.session_state.test_streak} / 5**")
        st.progress(st.session_state.test_streak / 5)
        st.caption("Acerte 5 seguidas para subir de nível!")
    
    if st.button("♻️ Reiniciar Tudo"):
        st.session_state.clear()
        st.rerun()

# --- 6. CONTEÚDO PRINCIPAL ---
st.title("🎙️ Gemini English Coach")

# Garante que sempre haja uma pergunta carregada
if st.session_state.frase_pt is None:
    proxima_pergunta()

# Botão principal sempre visível
if st.button("⏭️ PRÓXIMA PERGUNTA", type="primary"):
    proxima_pergunta()
    st.rerun()

if st.session_state.frase_pt:
    st.markdown("---")
    st.info(f"### Como se diz em Inglês?\n## {st.session_state.frase_pt}")

    # Áudio em Português automático (Cache Buster)
    if not st.session_state.audio_inicial_ok:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=True, label="Ouvindo desafio...")
        st.session_state.audio_inicial_ok = True
    else:
        play_audio(st.session_state.frase_pt, lang='pt', autoplay=False, label="Repetir desafio")

    st.divider()

    # Gravador com chave dinâmica
    audio_data = mic_recorder(
        start_prompt="🎤 Gravar Tradução", 
        stop_prompt="⏹️ Analisar", 
        key=f"mic_{st.session_state.audio_key}"
    )

    if audio_data:
        with st.spinner("Analisando..."):
            transcript = client.audio.transcriptions.create(
                file=("audio.wav", audio_data['bytes']), 
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
            f_prompt = f"Student said '{transcript}' for '{st.session_state.frase_en}'. Correct it in PT-BR. If correct, start with CORRETO."
            eval_text = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f_prompt}]
            ).choices[0].message.content
            st.session_state.feedback = {"falado": transcript, "texto": eval_text}

    if st.session_state.feedback:
        st.write(f"🗣️ **Você disse:** {st.session_state.feedback['falado']}")
        st.write(f"📝 **Feedback:** {st.session_state.feedback['texto']}")
        st.success(f"✅ **Gabarito:** {st.session_state.frase_en}")
        play_audio(st.session_state.frase_en, lang='en', label="Pronúncia Correta")

        # Lógica de Maestria: Só muda nível se acertar 5 no Modo Teste
        if "CORRETO" in st.session_state.feedback['texto'].upper():
            if st.session_state.modo == "Teste de Maestria":
                st.session_state.test_streak += 1
                if st.session_state.test_streak >= 5:
                    st.balloons()
                    if st.session_state.nivel_idx < len(DIFICULDADES) - 1:
                        st.session_state.nivel_idx += 1
                        st.session_state.test_streak = 0
                        st.success(f"Nível {DIFICULDADES[st.session_state.nivel_idx]['nivel']} desbloqueado!")
        else:
            if st.session_state.modo == "Teste de Maestria":
                st.error("Sequência resetada!")
                st.session_state.test_streak = 0

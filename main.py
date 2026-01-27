import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

# --- 2. MAPEAMENTO DE DIFICULDADE ---
DIFICULDADES = {
    "Begginer": {"instrucao": "Frases de 1 a 3 palavras simples.", "temp": 0.5},
    "basic": {"instrucao": "Frases simples no presente (I/You/He/She).", "temp": 0.6},
    "intermediate": {"instrucao": "Passado, futuro e conectores (because, although).", "temp": 0.7},
    "advanced": {"instrucao": "Phrasal verbs e expressões idiomáticas nativas.", "temp": 0.8},
    "professional": {"instrucao": "Linguagem corporativa e reuniões de negócios.", "temp": 0.9},
    "fluenty": {"instrucao": "Nível C2: gírias, nuances culturais e gramática complexa.", "temp": 1.0}
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 3. FUNÇÕES ---

def chamar_ia(prompt, temperatura=0.7):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura
        )
        return completion.choices[0].message.content
    except: return "Erro na conexão."

def transcrever_audio(audio_bytes):
    try:
        return client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3-turbo", response_format="text")
    except: return None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except: st.warning("Áudio indisponível.")

# --- 4. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'testes_concluidos' not in st.session_state: st.session_state.testes_concluidos = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None

# --- 5. INTERFACE ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Escolha sua Dificuldade Inicial")
    # O usuário pode escolher a dificuldade inicial, mas para subir terá que provar
    nivel_escolhido = st.selectbox("Selecione onde quer começar:", LISTA_NIVEIS)
    st.session_state.nivel = nivel_escolhido
    
    obj = st.selectbox("Seu foco:", ["Conversação Geral", "Negócios", "Viagens"])
    if st.button("Iniciar Treino ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'pratica'
        st.rerun()

elif st.session_state.step == 'pratica':
    # SIDEBAR COM O PROVADOR DE MAESTRIA
    with st.sidebar:
        st.title("🛡️ Prova de Maestria")
        st.write(f"Nível Atual: **{st.session_state.nivel}**")
        
        # Visualização dos 5 testes
        progresso = st.session_state.testes_concluidos
        st.write(f"Testes para subir de nível: **{progresso}/5**")
        cols = st.columns(5)
        for i in range(5):
            if i < progresso: cols[i].write("✅")
            else: cols[i].write("⚪")
        
        st.divider()
        if st.button("🔄 Trocar Nível Manualmente"):
            st.session_state.step = 'objetivo'
            st.session_state.testes_concluidos = 0
            st.rerun()

    st.title("🎙️ Prática de Inglês")

    # GERAR PERGUNTA
    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        st.session_state.aula_atual = None
        st.session_state.feedback = None
        config = DIFICULDADES[st.session_state.nivel]
        seed = random.randint(1, 9999)
        prompt = (f"Seed:{seed}. Nível {st.session_state.nivel}. {config['instrucao']}. "
                  f"Contexto: {st.session_state.obj_selecionado}. "
                  f"Responda: Phrase: [Inglês] | Translation: [Português]")
        
        res = chamar_ia(prompt, temperatura=config['temp'])
        if "|" in res:
            st.session_state.aula_atual = res
            st.session_state.mic_key += 1
            st.rerun()

    # EXIBIÇÃO
    if st.session_state.aula_atual:
        texto = st.session_state.aula_atual
        ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
        pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
        
        st.info(f"**Traduza:** {pt}")
        if st.button("🔊 Ouvir Original"): play_audio(ing)

        # GRAVAÇÃO
        audio = mic_recorder(start_prompt="🎤 Falar agora", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

        if audio:
            with st.spinner("Avaliando sua resposta..."):
                fala = transcrever_audio(audio['bytes'])
                if fala:
                    st.session_

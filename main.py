import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key.")

DIFICULDADES = {
    "Begginer": "Short phrases, basic greetings.",
    "basic": "Daily routines, simple present.",
    "intermediate": "Past events and future plans.",
    "advanced": "Complex opinions and idioms.",
    "professional": "Workplace scenarios and formal terms.",
    "fluenty": "Slang, metaphors, and native speed."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÕES ---

def chamar_ia(prompt, temp=1.0): # Temperatura máxima para máxima variedade
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            top_p=1.0 # Garante que ele explore mais o vocabulário
        )
        return completion.choices[0].message.content
    except: return "Erro na conexão."

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0

# --- 4. INTERFACE ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Configuração")
    st.session_state.nivel = st.selectbox("Escolha seu nível:", LISTA_NIVEIS)
    st.session_state.obj_selecionado = st.selectbox("Foco:", ["Social", "Business", "Travel"])
    if st.button("Iniciar ➡️"):
        st.session_state.step = 'app'
        st.rerun()

elif st.session_state.step == 'app':
    with st.sidebar:
        st.title("🕹️ Modos")
        if st.button("📖 Prática Diária"):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None # Limpa a frase ao trocar de modo
            st.rerun()
        if st.button("🏆 Teste de Nível"):
            st.session_state.modo = 'teste'
            st.session_state.test_streak = 0
            st.session_state.aula_atual = None
            st.rerun()
        st.write(f"Nível: **{st.session_state.nivel}**")

    # BOTÃO PRÓXIMA (O segredo está aqui)
    if st.button("⏭️ Nova Pergunta (Forçar)", type="primary") or st.session_state.aula_atual is None:
        st.session_state.aula_atual = None
        st.session_state.feedback = None
        
        # Geramos um código único para cada requisição
        unique_id = f"{time.time()}-{random.randint(1000, 9999)}"
        
        prompt = (f"Request ID: {unique_id}. "
                  f"Você deve gerar uma frase ÚNICA e INÉDITA em inglês. "
                  f"Nível: {st.session_state.nivel}. Contexto: {st.session_state.obj_selecionado}. "
                  f"Nunca repita frases anteriores. Varie os verbos e substantivos. "
                  f"Formato: Phrase: [Inglês] | Translation: [Português]")
        
        with st.spinner("Gerando conteúdo exclusivo..."):
            res = chamar_ia(prompt)
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.mic_key += 1
                st.rerun()

    # EXIBIÇÃO
    if st.session_state.aula_atual:
        texto = st.session_state.aula_atual
        try:
            ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.info(f"**Traduza:** {pt}")
            
            # Botão de áudio para conferir
            if st.button("🔊 Ouvir Original"):
                tts = gTTS(text=ing, lang='en')
                fp = BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp.getvalue(), format="audio/mp3")

            audio = mic_recorder(start_prompt="🎤 Gravar", stop_prompt="⏹️ Parar", key=f"mic_{st.session_state.mic_key}")
            # ... resto da lógica de correção ...
        except:
            st.write("Aguardando nova frase...")

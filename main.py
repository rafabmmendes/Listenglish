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
    st.error("Erro na API Key do Groq. Verifique os Secrets no Streamlit.")

# --- 2. FUNÇÕES DE SUPORTE ---

def transcrever_audio(audio_bytes):
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3-turbo", 
            response_format="text"
        )
        return transcription
    except Exception as e:
        st.error(f"Erro na transcrição: {e}")
        return None

def chamar_ia(prompt):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro: {e}"

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None

# --- 4. TELAS DO SISTEMA ---

# TELA 1: DEFINIÇÃO DE OBJETIVOS
if st.session_state.step == 'objetivo':
    st.title("🎯 Escolha seu Objetivo")
    objetivo = st.selectbox("O que você quer focar?", 
                            ["Inglês para Negócios (Business)", 
                             "Viagens (Travel)", 
                             "Conversaçãoimport streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

# --- 2. FUNÇÕES AUXILIARES ---

def transcrever_audio(audio_bytes):
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3-turbo", 
            response_format="text"
        )
        return transcription
    except Exception as e:
        return None

def chamar_ia(prompt):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro: {e}"

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0 # Chave para resetar o mic

# --- 4. FLUXO DE TELAS ---

# TELA: OBJETIVO
if st.session_state.step == 'objetivo':
    st.title("🎯 Escolha seu Objetivo")
    obj = st.selectbox("Foco do curso:", ["Business", "Travel", "Social"])
    if st.button("Iniciar Teste ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'teste_nivel'
        st.rerun()

# TELA: TESTE DE NÍVEL
elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste Rápido")
    pergunta = st.radio("Traduza: 'Eu gosto de café'", ["I like coffee", "I likes coffee"])
    if st.button("Finalizar"):
        st.session_state.nivel = "A2" if pergunta == "I like coffee" else "A1"
        st.session_state.step = 'pratica'
        st.rerun()

# TELA: PRÁTICA (Onde acontece o Reset)
elif st.session_state.step == 'pratica':
    with st.sidebar:
        st.title("👤 Perfil")
        st.write(f"Nível: **{st.session_state.nivel}**")
        st.progress(st.session_state.xp / 100)
        if st.button("🔄 Reiniciar"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🗣️ Pratique sua Fala")

    # BOTÃO PRÓXIMA: Aqui limpamos TUDO e mudamos a chave do mic
    if st.button("⏭️ Próxima Pergunta", type="primary"):
        with st.spinner("IA Gerando..."):
            prompt = f"Crie uma frase nível {st.session_state.nivel} sobre {st.session_state.obj_selecionado}. Formato: Phrase: [Inglês] | Translation: [Português]"
            st.session_state.aula_atual = chamar_ia(prompt)
            st.session_state.feedback = None
            st.session_state.texto_falado = None
            st.session_state.mic_key += 1 # ISSO FAZ O MICROFONE RESETAR
            st.rerun()

    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].strip()
            pt = texto.split("|")[1].split("Translation:")[-1].strip()
            
            st.info(f"**Traduza:** {pt}")
            if st.button("🔊 Ouvir Original"): play_audio(ing)

            # O MICROFONE USA A CHAVE QUE MUDA SEMPRE
            st.write("### 🎤 Grave agora:")
            audio = mic_recorder(start_prompt="Gravar", stop_prompt="Parar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("Analisando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno disse '{fala}' para '{ing}'. Avalie e se estiver certo diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        if "CORRETO" in st.session_state.feedback.upper():
                            st.session_state.xp += 25

            if st.session_state.texto_falado:
                st.write(f"🗣️ Você disse: {st.session_state.texto_falado}")
                st.write(f"📝 Feedback: {st.session_state.feedback}")
                st.write(f"✅ Gabarito: {ing}")
        except:
            st.error("Erro na lição. Clique em Próxima.")

if st.session_state.xp >= 100:
    st.balloons()
    st.session_state.xp = 0 # Sobe de nível na lógica anterior se desejar

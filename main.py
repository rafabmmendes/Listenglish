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
                             "Conversação Social", 
                             "Preparação para Entrevistas"])
    
    if st.button("Próximo: Teste de Nível ➡️"):
        st.session_state.obj_selecionado = objetivo
        st.session_state.step = 'teste_nivel'
        st.rerun()

# TELA 2: TESTE DE NIVELAMENTO
elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste de Nivelamento")
    st.write("Responda rapidamente para sabermos seu nível:")
    
    pergunta = st.radio("Como se diz 'Eu estou trabalhando agora'?", 
                        ["I work now", "I am working now", "I working now"])
    
    if st.button("Finalizar Teste"):
        if pergunta == "I am working now":
            st.session_state.nivel = "A2"
            st.success("Bom trabalho! Você começa no Nível A2.")
        else:
            st.session_state.nivel = "A1"
            st.info("Vamos começar do básico: Nível A1.")
        
        st.session_state.step = 'pratica'
        st.balloons()
        st.rerun()

# TELA 3: ÁREA DE PRÁTICA (SPEAKING)
elif st.session_state.step == 'pratica':
    # SIDEBAR
    with st.sidebar:
        st.title("👤 Seu Perfil")
        st.write(f"**Objetivo:** {st.session_state.obj_selecionado}")
        st.metric("Nível Atual", st.session_state.nivel)
        st.progress(st.session_state.xp / 100)
        if st.button("🔄 Reiniciar Curso"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🎙️ Treino de Fala")

    if st.button("⏭️ Próxima Pergunta", type="primary"):
        with st.spinner("IA Gerando lição..."):
            prompt = (f"Crie uma frase em inglês nível {st.session_state.nivel} sobre {st.session_state.obj_selecionado}. "
                      f"Responda APENAS: Phrase: [Inglês] | Translation: [Português]")
            st.session_state.aula_atual = chamar_ia(prompt)
            st.session_state.feedback = None
            st.session_state.texto_falado = None

    if st.session_state.aula_atual:
        st.markdown("---")
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].strip()
            pt = texto.split("|")[1].split("Translation:")[-1].strip()
            
            st.info(f"**Traduza e fale:** {pt}")
            
            if st.button("🔊 Ouvir Referência"):
                play_audio(ing)

            # GRAVADOR DE VOZ
            st.write("### 🎤 Sua vez de falar:")
            audio = mic_recorder(start_prompt="Gravar", stop_prompt="Parar", key='recorder')

            if audio:
                with st.spinner("Analisando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        # Prompt de correção
                        p_corr = f"O aluno disse '{fala}' para a frase '{ing}'. Corrija e dê dicas em PT-BR. Se estiver certo diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        if "CORRETO" in st.session_state.feedback.upper():
                            st.session_state.xp += 25

            if st.session_state.texto_falado:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                if "CORRETO" in st.session_state.feedback.upper():
                    st.success(st.session_state.feedback)
                else:
                    st.error(st.session_state.feedback)
                st.write(f"✅ **Gabarito:** {ing}")
        except:
            st.error("Erro ao carregar lição. Clique em Próxima.")

# Lógica de subir nível
if st.session_state.xp >= 100:
    st.session_state.xp = 0
    niveis = ["A1", "A2", "B1", "B2", "C1"]
    idx = niveis.index(st.session_state.nivel)
    if idx < len(niveis)-1:
        st.session_state.nivel = niveis[idx+1]
        st.balloons()

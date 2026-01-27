import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Erro na API Key. Verifique seus Secrets.")

# --- FUNÇÕES ---
def transcrever_audio(audio_bytes):
    """Usa o Groq (Whisper) para transformar áudio em texto"""
    try:
        # O Groq precisa de um 'arquivo' simulado
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="distil-whisper-large-v3-en", # Modelo de ouvido super rápido
            response_format="text"
        )
        return transcription
    except Exception as e:
        st.error(f"Erro na transcrição: {e}")
        return None

def corrigir_texto(texto_usuario, frase_correta):
    """Usa o Llama 3.3 para corrigir a frase transcrita"""
    prompt = (f"O aluno disse: '{texto_usuario}'. "
              f"A frase correta era: '{frase_correta}'. "
              f"Compare e dê um feedback curto em Português. "
              f"Se estiver perfeito ou muito próximo, comece com 'CORRETO'.")
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- ESTADO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Perfil")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    st.write(f"XP: {st.session_state.xp}/100")
    if st.button("🔄 Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- APP ---
st.title("🎙️ Treino de Fala com Groq")

# Botão para AVANÇAR PERGUNTA
if st.button("⏭️ Próxima Pergunta", type="primary"):
    with st.spinner("Gerando..."):
        try:
            prompt = (f"Gere uma frase em inglês nível {st.session_state.nivel}. "
                      f"Formato: Phrase: [Inglês] | Translation: [Português]")
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            res = completion.choices[0].message.content
            
            if "Phrase:" in res:
                st.session_state.aula_atual = res
                st.session_state.feedback = None
                st.session_state.texto_falado = None
            else:
                st.warning("Tente novamente.")
        except Exception as e:
            st.error(f"Erro: {e}")

# EXIBIÇÃO DA AULA
if st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ing = texto.split("|")[0].split("Phrase:")[-1].strip()
        pt = texto.split("|")[1].split("Translation:")[-1].strip()
        
        st.subheader("Fale em Inglês:")
        st.info(f"💡 {pt}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Ouvir Original"):
                play_audio(ing)
        
        st.write("### 🎤 Sua vez:")
        # Gravador de voz
        audio = mic_recorder(
            start_prompt="Gravar Resposta",
            stop_prompt="Parar e Enviar",
            key='recorder'
        )

        if audio:
            with st.spinner("Ouvindo e corrigindo..."):
                # 1. Transcreve o áudio
                texto_transcrito = transcrever_audio(audio['bytes'])
                
                if texto_transcrito:
                    st.session_state.texto_falado = texto_transcrito
                    
                    # 2. Corrige o texto
                    feedback = corrigir_texto(texto_transcrito, ing)
                    st.session_state.feedback = feedback
                    
                    # 3. Dá XP se acertou
                    if "CORRETO" in feedback.upper():
                        st.session_state.xp += 20
                        st.balloons()

        # Mostra resultados após a gravação
        if st.session_state.texto_falado:
            st.write("---")
            st.write(f"🗣️ **Você disse:** *{st.session_state.texto_falado}*")
            
        if st.session_state.feedback:
            if "CORRETO" in st.session_state.feedback.upper():
                st.success(st.session_state.feedback)
            else:
                st.error(st.session_state.feedback)
            st.write(f"✅ **Gabarito:** {ing}")

    except Exception as e:
        st.error(f"Erro ao processar lição: {e}")

# Evolução de Nível
if st.session_state.xp >= 100:
    st.session_state.xp = 0
    # Lógica simples de subir nível
    niveis = ["A1", "A2", "B1", "B2", "C1"]
    if st.session_state.nivel in niveis[:-1]:
        idx = niveis.index(st.session_state.nivel)
        st.session_state.nivel = niveis[idx+1]
        st.toast(f"Subiu para nível {st.session_state.nivel}!", icon="🎉")

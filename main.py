import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    # Certifique-se de que a chave GROQ_API_KEY está nos Secrets do Streamlit
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key do Groq. Verifique as configurações de Secrets.")

# --- 2. FUNÇÕES DE IA (GROQ) ---

def transcrever_audio(audio_bytes):
    """Transforma o áudio gravado em texto usando Whisper Turbo"""
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

def corrigir_fala(texto_usuario, frase_correta):
    """Compara o que foi dito com o gabarito usando Llama 3.3"""
    prompt = (
        f"O aluno deveria dizer: '{frase_correta}'. "
        f"O aluno disse: '{texto_usuario}'. "
        f"Avalie a precisão e dê um feedback curto em Português. "
        f"Se estiver correto ou muito próximo, comece a resposta com a palavra 'CORRETO'."
    )
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na análise: {e}"

def play_audio(text):
    """Gera áudio da frase correta para referência (gTTS)"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Player de áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- 4. INTERFACE LATERAL (PROGRESSO) ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível Atual", st.session_state.nivel)
    st.write(f"XP para o próximo nível: {st.session_state.xp}/100")
    st.progress(st.session_state.xp / 100)
    
    if st.button("🔄 Reiniciar Tudo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 5. ÁREA DE PRÁTICA
st.title("🎙️ Prática de Inglês (Groq Speed)")

# Botão de Avançar / Gerar
if st.button("⏭️ Próxima Pergunta", type="primary"):
    with st.spinner("Gerando novo desafio..."):
        try:
            prompt = (
                f"Gere uma frase curta em inglês nível {st.session_state.nivel}. "
                f"Formato obrigatório: Phrase: [Inglês] | Translation: [Português]"
            )
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
            
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.feedback = None
                st.session_state.texto_falado = None
            else:
                st.warning("Erro no formato da IA. Clique em 'Próxima' novamente.")
        except Exception as e:
            st.error(f"Erro ao conectar com Groq: {e}")

# Exibição da lição ativa
if st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ingles = texto.split("|")[0].split("Phrase:")[-1].strip()
        portugues = texto.split("|")[1].split("Translation:")[-1].strip()
        
        st.subheader("Traduza e Fale:")
        st.info(f"💡 {portugues}")
        
        if st.button("🔊 Ouvir Pronúncia"):
            play_audio(ingles)
        
        st.write("### 🎤 Grave sua resposta:")
        # Componente de microfone
        gravacao = mic_recorder(
            start_prompt="Clique para falar",
            stop_prompt="Parar e Corrigir",
            key='recorder_fala'
        )

        if gravacao:
            with st.spinner("IA processando sua voz..."):
                # Transcrição (Áudio para Texto)
                fala_texto = transcrever_audio(gravacao['bytes'])
                
                if fala_texto:
                    st.session_state.texto_falado = fala_texto
                    # Avaliação (Texto para Feedback)
                    feedback = corrigir_fala(fala_texto, ingles)
                    st.session_state.feedback = feedback
                    
                    # Ganho de XP
                    if "CORRETO" in feedback.upper():
                        st.session_state.xp += 25
                        st.balloons()

        # Resultados
        if st.session_state.texto_falado:
            st.write(f"🗣️ **Você disse:** *{st.session_state.texto_falado}*")
            
        if st.session_state.feedback:
            if "CORRETO" in st.session_state.feedback.upper():
                st.success(st.session_state.feedback)
            else:
                st.error(st.session_state.feedback)
            st.write(f"✅ **Gabarito:** {ingles}")

    except Exception as e:
        st.error("Erro ao carregar os dados da lição.")

# Lógica de subir de nível (CEFR)
niveis_map = ["A1", "A2", "B1", "B2", "C1", "C2"]
if st.session_state.xp >= 100:
    idx = niveis_map.index(st.session_state.nivel)
    if idx < len(niveis_map) - 1:
        st.session_state.nivel = niveis_map[idx+1]
        st.session_state.xp = 0
        st.toast(f"Parabéns! Você subiu para o nível {st.session_state.nivel}!", icon="🎉")

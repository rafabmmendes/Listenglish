import streamlit as st
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

# --- 2. FUNÇÕES DE IA ---

def transcrever_audio(audio_bytes):
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3-turbo", 
            response_format="text"
        )
        return transcription
    except:
        return None

def chamar_ia(prompt):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
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
# Lista de níveis personalizada por você
niveis_lista = ["Begginer", "basic", "intermediate", "advanced", "professional", "fluenty"]

if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- 4. FLUXO DE TELAS ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Objetivo do Curso")
    obj = st.selectbox("O que você quer praticar?", ["Business English", "Travel", "Daily Conversations"])
    if st.button("Ir para Teste ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'teste_nivel'
        st.rerun()

elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste de Nível")
    pergunta = st.radio("Como se diz 'Eu tenho um carro'?", ["I have a car", "I has a car"])
    if st.button("Finalizar Teste"):
        # Se acertar, pula para 'basic', se errar fica no 'Begginer'
        st.session_state.nivel = "basic" if pergunta == "I have a car" else "Begginer"
        st.session_state.step = 'pratica'
        st.rerun()

elif st.session_state.step == 'pratica':
    with st.sidebar:
        st.title("👤 Seu Perfil")
        st.info(f"Nível: **{st.session_state.nivel}**")
        st.write(f"XP: {st.session_state.xp}/100")
        st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
        if st.button("🔄 Reiniciar App"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🗣️ Treino Infinito")

    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("Gerando novo desafio..."):
            st.session_state.aula_atual = None
            st.session_state.feedback = None
            st.session_state.texto_falado = None
            
            seed = random.randint(1, 999999)
            prompt = (f"Seed:{seed}. Gere uma frase única em inglês para nível {st.session_state.nivel} "
                      f"sobre {st.session_state.obj_selecionado}. "
                      f"Responda APENAS no formato: Phrase: [Inglês] | Translation: [Português]")
            
            res = chamar_ia(prompt)
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.mic_key += 1
                st.rerun()

    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.info(f"**Traduza:** {pt}")
            if st.button("🔊 Ouvir Resposta"):
                play_audio(ing)

            st.write("---")
            st.write("### 🎤 Grave sua voz:")
            audio = mic_recorder(start_prompt="Gravar", stop_prompt="Parar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("Analisando pronúncia..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno disse '{fala}' para a frase '{ing}'. Dê um feedback curto. Se estiver certo, diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        if "CORRETO" in st.session_state.feedback.upper():
                            st.session_state.xp += 25

            if st.session_state.texto_falado:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                if st.session_state.feedback:
                    st.write(f"📝 **Feedback:** {st.session_state.feedback}")
                st.write(f"✅ **Gabarito:** {ing}")
                
            # Lógica de Nível Up com a nova lista
            if st.session_state.xp >= 100:
                st.balloons()
                st.session_state.xp = 0
                idx = niveis_lista.index(st.session_state.nivel)
                if idx < len(niveis_lista) - 1:
                    st.session_state.nivel = niveis_lista[idx + 1]
                    st.success(f"Excelente! Você agora é nível {st.session_state.nivel}!")

        except Exception as e:
            st.error("Erro ao processar lição. Clique em Próxima Pergunta.")

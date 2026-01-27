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
            temperature=0.8
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
niveis_lista = ["Begginer", "basic", "intermediate", "advanced", "professional", "fluenty"]

# Regras de dificuldade para a IA
diretrizes_dificuldade = {
    "Begginer": "Use apenas 2 ou 3 palavras. Coisas ultra básicas como 'Blue sky' ou 'Thank you'.",
    "basic": "Frases simples no presente. Ex: 'I like coffee' ou 'He lives here'.",
    "intermediate": "Frases com conectores (and, but, because) e passado/futuro simples.",
    "advanced": "Use expressões idiomáticas (idioms), phrasal verbs e gramática complexa.",
    "professional": "Foco em vocabulário corporativo, reuniões e termos formais de trabalho.",
    "fluenty": "Frases longas, complexas, com nuances culturais e vocabulário erudito."
}

if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- 4. FLUXO DE TELAS ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Escolha seu Objetivo")
    obj = st.selectbox("Foco do treino:", ["Daily Social", "Business English", "Travel", "Job Interview"])
    if st.button("Confirmar e Testar Nível ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'teste_nivel'
        st.rerun()

elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste de Nivelamento")
    st.write("Como se diz 'Eu estou feliz' em inglês?")
    pergunta = st.radio("Escolha a opção:", ["I am happy", "I happy"])
    if st.button("Finalizar Teste"):
        st.session_state.nivel = "basic" if pergunta == "I am happy" else "Begginer"
        st.session_state.step = 'pratica'
        st.rerun()

elif st.session_state.step == 'pratica':
    with st.sidebar:
        st.title("👤 Seu Progresso")
        st.info(f"Nível: **{st.session_state.nivel}**")
        st.write(f"XP para o próximo nível: {st.session_state.xp}/100")
        st.progress(st.session_state.xp / 100)
        if st.button("🔄 Reiniciar Tudo"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🎙️ Treino Infinito")

    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("IA preparando sua lição..."):
            st.session_state.aula_atual = None
            st.session_state.feedback = None
            st.session_state.texto_falado = None
            
            seed = random.randint(1, 9999)
            regra = diretrizes_dificuldade.get(st.session_state.nivel, "")
            
            prompt = (f"Seed:{seed}. Você é um professor de inglês. "
                      f"Gere uma frase para o nível {st.session_state.nivel}. "
                      f"Instrução de dificuldade: {regra}. "
                      f"Contexto: {st.session_state.obj_selecionado}. "
                      f"Responda APENAS: Phrase: [Inglês] | Translation: [Português]")
            
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
            
            st.markdown(f"### Como se diz:\n> **{pt}**")
            
            if st.button("🔊 Ouvir Pronúncia"):
                play_audio(ing)

            st.write("---")
            audio = mic_recorder(start_prompt="🎤 Gravar Resposta", stop_prompt="⏹️ Parar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("Avaliando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno deveria dizer '{ing}' mas disse '{fala}'. Dê um feedback curto em português e se estiver certo diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        if "CORRETO" in st.session_state.feedback.upper():
                            st.session_state.xp += 25

            if st.session_state.texto_falado:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                if st.session_state.feedback:
                    st.write(f"📝 **Feedback:** {st.session_state.feedback}")
                st.write(f"✅ **Gabarito:** {ing}")
                
            if st.session_state.xp >= 100:
                st.balloons()
                st.session_state.xp = 0
                idx = niveis_lista.index(st.session_state.nivel)
                if idx < len(niveis_lista) - 1:
                    st.session_state.nivel = niveis_lista[idx + 1]
                    st.success(f"Parabéns! Você subiu para o nível: {st.session_state.nivel}")

        except Exception as e:
            st.error("Erro na lição. Clique em Próxima Pergunta.")

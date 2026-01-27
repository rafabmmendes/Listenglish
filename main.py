import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time # Importado para gerar timestamps únicos
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key.")

DIFICULDADES = {
    "Begginer": "Short phrases (2-3 words). No complex grammar.",
    "basic": "Simple sentences in present tense.",
    "intermediate": "Use past and future with connectors like 'because'.",
    "advanced": "Native idioms and phrasal verbs.",
    "professional": "Corporate and formal business vocabulary.",
    "fluenty": "C2 level: slang, complex cultural nuances, and metaphors."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÕES DE APOIO ---

def chamar_ia(prompt, temp=0.9): # Aumentamos a temperatura para 0.9 para mais variedade
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return completion.choices[0].message.content
    except: return "Erro na conexão."

def transcrever_audio(audio_bytes):
    try:
        res = client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3-turbo", response_format="text")
        return res
    except: return None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except: st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = random.randint(0, 1000)
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

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
        if st.button("📖 Prática Diária", use_container_width=True):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None
            st.rerun()
            
        if st.button("🏆 Teste de Nível", use_container_width=True):
            st.session_state.modo = 'teste'
            st.session_state.test_streak = 0
            st.session_state.aula_atual = None
            st.rerun()
            
        st.divider()
        st.write(f"Nível: **{st.session_state.nivel}**")
        if st.session_state.modo == 'teste':
            st.warning(f"Streak: {st.session_state.test_streak}/5")
            st.progress(st.session_state.test_streak / 5)

    # BOTÃO DE PRÓXIMA PERGUNTA (O motor de troca)
    if st.button("⏭️ Gerar Nova Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("Sorteando novo desafio..."):
            # Limpeza total do estado anterior
            st.session_state.aula_atual = None
            st.session_state.feedback = None
            st.session_state.texto_falado = None
            
            # Criar um marcador único para evitar cache
            marcador_unico = time.time()
            
            # Prompt com instrução de aleatoriedade forçada
            prompt = (f"Timestamp: {marcador_unico}. Gere uma frase TOTALMENTE NOVA em inglês para o nível {st.session_state.nivel}. "
                      f"Instrução: {DIFICULDADES[st.session_state.nivel]}. "
                      f"Contexto: {st.session_state.obj_selecionado}. "
                      f"Importante: Não repita frases anteriores. "
                      f"Responda EXCLUSIVAMENTE no formato: Phrase: [Inglês] | Translation: [Português]")
            
            res = chamar_ia(prompt)
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.mic_key = random.randint(0, 9999) # Força o widget do mic a resetar
                st.rerun()

    # ÁREA DA LIÇÃO
    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.markdown(f"### Como você diz em inglês?\n> **{pt}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Ouvir Original"): play_audio(ing)
            
            st.write("---")
            audio = mic_recorder(start_prompt="🎤 Gravar Resposta", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("Avaliando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno disse '{fala}' para a frase '{ing}'. Dê um feedback curto. Se estiver correto diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        
                        if "CORRETO" in st.session_state.feedback.upper():
                            if st.session_state.modo == 'teste':
                                st.session_state.test_streak += 1
                                if st.session_state.test_streak >= 5:
                                    st.balloons()
                                    idx = LISTA_NIVEIS.index(st.session_state.nivel)
                                    if idx < len(LISTA_NIVEIS)-1:
                                        st.session_state.nivel = LISTA_NIVEIS[idx+1]
                                        st.session_state.modo = 'pratica'
                                        st.session_state.test_streak = 0
                                        st.success(f"🏆 MAESTRIA! Você subiu para {st.session_state.nivel}!")
                                        time.sleep(2)
                                        st.rerun()
                            else:
                                st.success("Correto! Pratique mais ou tente o Teste de Nível.")
                        else:
                            if st.session_state.modo == 'teste':
                                st.error("❌ Erro no teste! Voltando para a Prática.")
                                st.session_state.modo = 'pratica'
                                st.session_state.test_streak = 0

            if st.session_state.feedback:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                st.write(f"📝 **Feedback:** {st.session_state.feedback}")
                st.write(f"✅ **Gabarito:** {ing}")
        except:
            st.error("Erro na lição. Tente o botão 'Próxima Pergunta'.")

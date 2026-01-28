import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

DIFICULDADES = {
    "Begginer": "Short phrases, simple greetings.",
    "basic": "Daily routines, simple present.",
    "intermediate": "Past/Future events and connectors.",
    "advanced": "Complex idioms and phrasal verbs.",
    "professional": "Workplace scenarios and formal terms.",
    "fluenty": "Slang, metaphors, and native nuances."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÃO DE ÁUDIO COM AUTOPLAY ---
def play_audio(text, autoplay=False):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        data = fp.getvalue()
        b64 = base64.b64encode(data).decode()
        
        # HTML para permitir o autoplay automático
        md = f"""
            <audio controls {"autoplay" if autoplay else ""} style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning("Áudio indisponível no momento.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'autoplay_done' not in st.session_state: st.session_state.autoplay_done = False

# --- 4. TELAS ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Configuração")
    st.session_state.nivel = st.selectbox("Escolha seu nível:", LISTA_NIVEIS)
    st.session_state.obj_selecionado = st.selectbox("Foco:", ["Social", "Business", "Travel"])
    if st.button("Iniciar ➡️"):
        st.session_state.step = 'app'
        st.rerun()

elif st.session_state.step == 'app':
    with st.sidebar:
        st.title("⚙️ Opções")
        if st.button("📖 Prática Diária"):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None
            st.rerun()
        if st.button("🏆 Teste de Nível"):
            st.session_state.modo = 'teste'
            st.session_state.test_streak = 0
            st.session_state.aula_atual = None
            st.rerun()
        st.write(f"Nível: **{st.session_state.nivel}**")

    st.title("🗣️ Treino de Fala")

    # GERAR PERGUNTA
    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("IA criando desafio..."):
            unique_seed = f"{time.time()}-{random.randint(1, 9999)}"
            prompt = (f"Seed: {unique_seed}. Create a UNIQUE English sentence for level {st.session_state.nivel}. "
                      f"Topic: {st.session_state.obj_selecionado}. Rule: {DIFICULDADES[st.session_state.nivel]}. "
                      f"Format: Phrase: [English] | Translation: [Portuguese]")
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0
            )
            st.session_state.aula_atual = completion.choices[0].message.content
            st.session_state.mic_key += 1
            st.session_state.feedback = None
            st.session_state.autoplay_done = False # Reseta para tocar na próxima
            st.rerun()

    # EXIBIÇÃO E ÁUDIO
    if st.session_state.aula_atual and "|" in st.session_state.aula_atual:
        res_ia = st.session_state.aula_atual
        ing = res_ia.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
        pt = res_ia.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
        
        st.info(f"**Traduza para o Inglês:**\n### {pt}")
        
        # LÓGICA DE ÁUDIO
        st.write("🔊 **Áudio da Resposta:**")
        if not st.session_state.autoplay_done:
            play_audio(ing, autoplay=True)
            st.session_state.autoplay_done = True # Garante que só toque sozinho uma vez
        else:
            play_audio(ing, autoplay=False) # Botão para repetir manualmente
        
        st.divider()

        # GRAVAÇÃO
        audio = mic_recorder(start_prompt="🎤 Clique para Gravar sua voz", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

        if audio:
            with st.spinner("Avaliando..."):
                transcript = client.audio.transcriptions.create(
                    file=("audio.wav", audio['bytes']), 
                    model="whisper-large-v3-turbo", 
                    response_format="text"
                )
                
                f_prompt = f"The student said '{transcript}' for '{ing}'. Correct in Portuguese. If 100% correct, start with CORRETO."
                feedback_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f_prompt}])
                feedback_text = feedback_res.choices[0].message.content

                st.write(f"🗣️ **Você disse:** {transcript}")
                st.write(f"📝 **Feedback:** {feedback_text}")
                st.write(f"✅ **Gabarito:** {ing}")

                if "CORRETO" in feedback_text.upper():
                    if st.session_state.modo == 'teste':
                        st.session_state.test_streak += 1
                        if st.session_state.test_streak >= 5:
                            st.balloons()
                            idx = LISTA_NIVEIS.index(st.session_state.nivel)
                            if idx < len(LISTA_NIVEIS) - 1:
                                st.session_state.nivel = LISTA_NIVEIS[idx+1]
                                st.session_state.test_streak = 0
                                st.session_state.aula_atual = None
                                st.success(f"Nível UP: {st.session_state.nivel}!")
                    else:
                        st.success("Correto!")
                else:
                    if st.session_state.modo == 'teste':
                        st.error("Erro no teste. Streak resetado.")
                        st.session_state.test_streak = 0

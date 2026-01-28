import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key.")

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
def play_audio(text, lang='en', autoplay=False, label="Ouvir"):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        data = fp.getvalue()
        b64 = base64.b64encode(data).decode()
        
        md = f"""
            <div style="margin-bottom: 10px;">
                <p style="margin-bottom: 5px; font-size: 0.9em; color: gray;">{label} ({lang})</p>
                <audio controls {"autoplay" if autoplay else ""} style="width: 100%; height: 35px;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.warning(f"Áudio ({lang}) indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'autoplay_pt_done' not in st.session_state: st.session_state.autoplay_pt_done = False
if 'show_english_audio' not in st.session_state: st.session_state.show_english_audio = False

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
        st.title("⚙️ Opções")
        if st.button("📖 Prática Diária"):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None
            st.rerun()
        if st.button("🏆 Teste de Nível"):
            st.session_state.modo = 'teste'
            st.session_state.aula_atual = None
            st.rerun()
        st.write(f"Nível: **{st.session_state.nivel}**")

    st.title("🗣️ Treino de Tradução Oral")

    # GERAR PERGUNTA
    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("IA criando desafio..."):
            seed = f"{time.time()}-{random.randint(1, 9999)}"
            prompt = (f"Seed: {seed}. Create a UNIQUE sentence for {st.session_state.nivel} level. "
                      f"Topic: {st.session_state.obj_selecionado}. Rule: {DIFICULDADES[st.session_state.nivel]}. "
                      f"Format: Phrase: [English] | Translation: [Portuguese]")
            
            completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=1.0)
            st.session_state.aula_atual = completion.choices[0].message.content
            st.session_state.mic_key += 1
            st.session_state.autoplay_pt_done = False 
            st.session_state.show_english_audio = False # Esconde o áudio em inglês no início
            st.session_state.feedback = None
            st.rerun()

    # EXIBIÇÃO E LÓGICA DE ÁUDIO
    if st.session_state.aula_atual and "|" in st.session_state.aula_atual:
        res_ia = st.session_state.aula_atual
        ing = res_ia.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
        pt = res_ia.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
        
        # 1. ÁUDIO EM PORTUGUÊS (O DESAFIO)
        st.subheader("Traduza o que você ouvir:")
        if not st.session_state.autoplay_pt_done:
            play_audio(pt, lang='pt', autoplay=True, label="Desafio em Português")
            st.session_state.autoplay_pt_done = True
        else:
            play_audio(pt, lang='pt', autoplay=False, label="Repetir Desafio")
        
        st.info(f"❓ **Em português:** {pt}")
        st.divider()

        # 2. GRAVAÇÃO DO USUÁRIO
        audio = mic_recorder(start_prompt="🎤 Gravar tradução em Inglês", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

        if audio:
            with st.spinner("Analisando..."):
                transcript = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3-turbo", response_format="text")
                f_prompt = f"The student said '{transcript}' for '{ing}'. Correct in Portuguese. If 100% correct, start with CORRETO."
                feedback_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f_prompt}])
                st.session_state.feedback = feedback_res.choices[0].message.content
                st.session_state.texto_falado = transcript
                st.session_state.show_english_audio = True # Libera o áudio em inglês agora

        # 3. FEEDBACK E ÁUDIO EM INGLÊS (O GABARITO)
        if st.session_state.show_english_audio:
            st.write("---")
            st.success("✅ **Gabarito e Pronúncia Correta:**")
            st.write(f"**Frase correta:** {ing}")
            play_audio(ing, lang='en', autoplay=False, label="Ouvir pronúncia oficial")
            
            if st.session_state.feedback:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                st.write(f"📝 **Feedback:** {st.session_state.feedback}")

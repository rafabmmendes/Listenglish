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
    st.error("Erro na API Key. Verifique seus Secrets no Streamlit.")

DIFICULDADES = {
    "Begginer": "Very simple words, greetings only.",
    "basic": "Simple present tense sentences.",
    "intermediate": "Past/Future and connectors.",
    "advanced": "Idioms and phrasal verbs.",
    "professional": "Business English and formal terms.",
    "fluenty": "Native slang and complex metaphors."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0

# --- 3. TELAS ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Configuração do Curso")
    st.session_state.nivel = st.selectbox("Nível Inicial:", LISTA_NIVEIS)
    st.session_state.obj_selecionado = st.selectbox("Foco:", ["Social", "Business", "Travel"])
    if st.button("Começar Treino ➡️"):
        st.session_state.step = 'app'
        st.rerun()

elif st.session_state.step == 'app':
    # Barra Lateral
    with st.sidebar:
        st.title("⚙️ Painel")
        if st.button("📖 Prática Diária"):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None
            st.rerun()
        if st.button("🏆 Teste de Nível"):
            st.session_state.modo = 'teste'
            st.session_state.test_streak = 0
            st.session_state.aula_atual = None
            st.rerun()
        
        st.divider()
        st.write(f"Nível: **{st.session_state.nivel}**")
        if st.session_state.modo == 'teste':
            st.write(f"Progresso: {st.session_state.test_streak}/5")
            st.progress(st.session_state.test_streak / 5)

    st.title("🗣️ Treino de Inglês")

    # Botão de Gerar Pergunta
    if st.button("⏭️ Gerar Nova Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("IA criando frase inédita..."):
            # O Segredo para mudar a frase: Seed única no prompt
            unique_seed = f"{time.time()}-{random.randint(1, 9999)}"
            prompt = (f"Seed: {unique_seed}. Create a UNIQUE English sentence for level {st.session_state.nivel}. "
                      f"Topic: {st.session_state.obj_selecionado}. Instructions: {DIFICULDADES[st.session_state.nivel]}. "
                      f"Always use different verbs and nouns. "
                      f"Format: Phrase: [English] | Translation: [Portuguese]")
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0
            )
            st.session_state.aula_atual = completion.choices[0].message.content
            st.session_state.mic_key += 1
            st.session_state.feedback = None
            st.rerun() # Força o app a mostrar a frase nova imediatamente

    # EXIBIÇÃO DA PERGUNTA (Sempre visível se aula_atual existir)
    if st.session_state.aula_atual and "|" in st.session_state.aula_atual:
        try:
            res_ia = st.session_state.aula_atual
            ing = res_ia.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = res_ia.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.subheader(f"Como se diz em inglês?")
            st.info(f"### {pt}")
            
            if st.button("🔊 Ouvir Pronúncia"):
                tts = gTTS(text=ing, lang='en')
                fp = BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp.getvalue(), format="audio/mp3")

            st.divider()
            
            # Gravador de Áudio
            audio = mic_recorder(
                start_prompt="🎤 Clique para falar", 
                stop_prompt="⏹️ Parar e Analisar", 
                key=f"mic_{st.session_state.mic_key}"
            )

            if audio:
                with st.spinner("Analisando sua fala..."):
                    # Transcrição
                    transcript = client.audio.transcriptions.create(
                        file=("audio.wav", audio['bytes']), 
                        model="whisper-large-v3-turbo", 
                        response_format="text"
                    )
                    
                    # Feedback
                    f_prompt = f"The student said '{transcript}' for the sentence '{ing}'. Correct it in Portuguese. If it is 100% correct, start with the word CORRETO."
                    feedback_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f_prompt}]
                    )
                    feedback_text = feedback_res.choices[0].message.content

                    st.write(f"🗣️ **Você disse:** {transcript}")
                    st.write(f"📝 **Análise:** {feedback_text}")
                    st.write(f"✅ **Gabarito:** {ing}")

                    # Lógica de Nível
                    if "CORRETO" in feedback_text.upper():
                        if st.session_state.modo == 'teste':
                            st.session_state.test_streak += 1
                            if st.session_state.test_streak >= 5:
                                st.balloons()
                                idx = LISTA_NIVEIS.index(st.session_state.nivel)
                                if idx < len(LISTA_NIVEIS) - 1:
                                    st.session_state.nivel = LISTA_NIVEIS[idx+1]
                                    st.success(f"Uau! Você subiu para o nível {st.session_state.nivel}!")
                                    st.session_state.test_streak = 0
                                    st.session_state.aula_atual = None
                        else:
                            st.success("Parabéns! Continue praticando.")
                    else:
                        if st.session_state.modo == 'teste':
                            st.error("Erro no teste. Reiniciando sequência...")
                            st.session_state.test_streak = 0

        except Exception as e:
            st.warning("Houve um pequeno erro na formatação da IA. Clique em 'Gerar Nova Pergunta'.")

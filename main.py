import streamlit as st
from gtts import gTTS
from io import BytesIO

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- BANCO DE DADOS DE LIÇÕES ---
db_lessons = {
    "Business (Trabalho)": [
        {"type": "repeat", "en": "Nice to meet you. I am the project manager.", "instruction": "Apresente-se formalmente:"},
        {"type": "translate", "pt": "Você pode me enviar o relatório?", "en": "Can you send me the report?", "instruction": "Traduza para o Inglês:"},
        {"type": "qa", "audio_en": "Are you available for a call at 3 PM?", "en": "3 PM", "instruction": "A IA te perguntou algo. Responda se está disponível às 3h:"},
        {"type": "repeat", "en": "We need to brainstorm some new marketing strategies.", "instruction": "Repita este termo avançado (Brainstorm):"}
    ],
    "Travel (Viagem)": [
        {"type": "repeat", "en": "Where is the boarding gate?", "instruction": "Pergunte sobre o portão de embarque:"},
        {"type": "translate", "pt": "Eu gostaria de um copo de água.", "en": "I would like a glass of water.", "instruction": "Peça água em inglês:"}
    ]
}

# --- LÓGICA DE NAVEGAÇÃO ---
if 'step' not in st.session_state:
    st.session_state.step = 'objective'
if 'practice_idx' not in st.session_state:
    st.session_state.practice_idx = 0

# --- TELA INICIAL ---
if st.session_state.step == 'objective':
    st.title("💼 LinguistAI - Business Edition")
    obj = st.selectbox("Selecione seu foco:", list(db_lessons.keys()))
    if st.button("Começar Treinamento"):
        st.session_state.objective = obj
        st.session_state.step = 'practice'
        st.rerun()

# --- TELA DE PRÁTICA ---
elif st.session_state.step == 'practice':
    content = db_lessons[st.session_state.objective]
    idx = st.session_state.practice_idx
    
    if idx < len(content):
        item = content[idx]
        st.subheader(f"Lição {idx + 1} de {len(content)}")
        st.info(item['instruction'])
        
        # Lógica por tipo de exercício
        if item['type'] == 'repeat':
            play_audio(item['en'])
            st.write(f"🗣️ **Diga:** {item['en']}")
        
        elif item['type'] == 'translate':
            st.write(f"🇧🇷 {item['pt']}")
            resp = st.text_input("Sua resposta escrita (simulando fala):", key=f"input_{idx}")
            if st.button("Check"):
                if item['en'].lower() in resp.lower(): st.success("Perfeito!")
                else: st.warning(f"O correto é: {item['en']}")

        elif item['type'] == 'qa':
            play_audio(item['audio_en'])
            resp_qa = st.text_input("Sua resposta à pergunta:", key=f"qa_{idx}")

        if st.button("Próxima Lição ➡️"):
            st.session_state.practice_idx += 1
            st.rerun()
    else:
        st.success("🎉 Você concluiu sua meta diária de Business English!")
        if st.button("Voltar ao Menu"):
            st.session_state.step = 'objective'
            st.session_state.practice_idx = 0
            st.rerun()

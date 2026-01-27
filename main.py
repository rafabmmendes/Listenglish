import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ---
try:
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro na API Key. Verifique os Secrets.")

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp.getvalue(), format="audio/mp3")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível Atual", st.session_state.nivel)
    st.write(f"**XP:** {st.session_state.xp}")
    if st.button("Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELA 1: SETUP ---
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("Seu objetivo:", ["Business", "Travel", "Social"])
    if st.button("Iniciar Teste de Nível"):
        st.session_state.obj = obj
        with st.spinner("Gerando desafio..."):
            prompt = f"Generate a unique B1 level English sentence about {obj}."
            st.session_state.frase_teste = model.generate_content(prompt).text
            st.session_state.step = 'test'
            st.rerun()

# --- TELA 2: TESTE COM VALIDAÇÃO (NÃO PASSA SE ERRAR FEIO) ---
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nivelamento")
    st.write("Ouça a frase e escreva exatamente o que ouviu ou a tradução correta:")
    play_audio(st.session_state.frase_teste)
    
    res_user = st.text_input("Sua resposta:")
    
    if st.button("Avaliar meu Nível"):
        if res_user:
            with st.spinner("Analisando precisão..."):
                # Pedimos para a IA avaliar se a resposta é aceitável ou um erro total
                check_prompt = f"The correct sentence was '{st.session_state.frase_teste}'. The user wrote '{res_user}'. Is this a reasonable understanding? Answer with 'YES' or 'NO' followed by the CEFR level (A1-C1)."
                result = model.generate_content(check_prompt).text.strip().upper()
                
                if "NO" in result:
                    st.error("❌ Você errou muito a frase! Tente ouvir novamente ou revise o básico.")
                    st.session_state.nivel = "A1 (Iniciante)"
                else:
                    st.success("✅ Boa compreensão!")
                    # Extrai o nível (ex: B1) do texto da IA
                    st.session_state.nivel = "".join([c for c in result if c in "ABC12"])[:2]
                    st.session_state.step = 'practice'
                    st.rerun()
        else:
            st.warning("Escreva algo antes de continuar!")

# --- TELA 3: PRÁTICA ---
elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    st.info(f"Treinando em nível: {st.session_state.nivel}")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("Criando..."):
            seed = random.randint(1, 9999)
            prompt = f"New English phrase level {st.session_state.nivel} for {st.session_state.obj}. Seed: {seed}. Format: Phrase: [English] | Translation: [Portuguese]"
            st.session_state.aula_atual = model.generate_content(prompt).text
            st.session_state.xp += 10

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            ingles = st.session_state.aula_atual.split("|")[0].replace("Phrase:", "").strip()
            portugues = st.session_state.aula_atual.split("|")[1].replace("Translation:", "").strip()
            st.write(f"**Traduza:** {portugues}")
            if st.button("🔊 Ver resposta e ouvir"):
                play_audio(ingles)
                st.success(f"Inglês: {ingles}")

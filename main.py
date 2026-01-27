import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ---
@st.cache_resource
def load_model():
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = load_model()

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível no momento.")

# --- SISTEMA DE EVOLUÇÃO ---
def check_level_up():
    niveis = ["A1", "A2", "B1", "B2", "C1", "C2"]
    if st.session_state.xp >= 100:
        atual = st.session_state.nivel
        if atual in niveis and atual != "C2":
            novo_index = niveis.index(atual) + 1
            st.session_state.nivel = niveis[novo_index]
            st.session_state.xp = 0 
            st.balloons()
            st.success(f"🎊 NÍVEL UP! Você agora está no {st.session_state.nivel}!")

# --- INICIALIZAÇÃO DO ESTADO ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Progresso")
    st.metric("Nível", st.session_state.nivel)
    st.write(f"XP para o próximo nível:")
    st.progress(st.session_state.xp / 100)
    st.write(f"**{st.session_state.xp} / 100**")
    
    if st.button("🔄 Reiniciar Tudo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS ---

if st.session_state.step == 'setup':
    st.title("🎧 LinguistAI")
    obj = st.selectbox("O que quer praticar?", ["Business", "Travel", "Social"])
    if st.button("Começar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treino")
    check_level_up()
    
    # BOTÃO PARA GERAR NOVA LIÇÃO
    if st.button("✨ Gerar Nova Frase"):
        with st.spinner("IA buscando nova lição..."):
            try:
                seed = random.randint(1, 10000)
                prompt = (f"Level {st.session_state.nivel} English sentence about {st.session_state.obj}. "
                          f"Format: Phrase: [English] | Translation: [Portuguese]. Seed: {seed}")
                res = model.generate_content(prompt)
                if res.text:
                    st.session_state.aula_atual = res.text
                    st.session_state.xp += 20 # Ganha XP a cada nova lição
            except Exception as e:
                st.error("Cota de IA atingida. Aguarde 15 segundos.")

    # MOSTRAR A LIÇÃO (Se ela existir no estado)
    if st.session_state.aula_atual:
        st.markdown("---")
        try:
            texto = st.session_state.aula_atual
            if "|" in texto:
                partes = texto.split("|")
                # Extração limpa do texto
                ing = partes[0].split(":")[-1].strip()
                pt = partes[1].split(":")[-1].strip()
                
                st.subheader("Tradução:")
                st.info(pt)
                
                if st.button("🔊 Ouvir Pronúncia e Ver Inglês"):
                    play_audio(ing)
                    st.success(f"**Inglês:** {ing}")
            else:
                st.write(texto)
        except:
            st.error("Erro ao formatar a lição. Tente gerar outra.")

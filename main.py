import streamlit as st
from groq import Groq # Troque google.generativeai por groq
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO GROQ ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def chamar_ia(prompt):
    # O Groq usa uma sintaxe parecida com o ChatGPT
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- INICIALIZAÇÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Seu Perfil (Groq Speed)")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    if st.button("🔄 Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("⚡ LinguistAI com Groq")

if st.button("✨ Gerar Nova Lição"):
    with st.spinner("IA ultra-rápida pensando..."):
        try:
            prompt = f"Crie uma frase em inglês nível {st.session_state.nivel}. Responda APENAS no formato: Phrase: [Inglês] | Translation: [Português]"
            # Usando a função do Groq que criamos acima
            res = chamar_ia(prompt)
            st.session_state.aula_atual = res
            st.session_state.xp += 20
        except Exception as e:
            st.error(f"Erro no Groq: {e}")

if 'aula_atual' in st.session_state and st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        ing = texto.split("|")[0].split(":")[-1].strip()
        pt = texto.split("|")[1].split(":")[-1].strip()
        
        st.subheader("Traduza:")
        st.info(pt)
        
        if st.button("🔊 Ver Resposta e Ouvir"):
            st.success(ing)
            play_audio(ing)
    except:
        st.error("Erro ao formatar lição.")

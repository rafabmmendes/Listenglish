import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO GROQ ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Erro na API Key do Groq. Verifique os Secrets.")

def chamar_ia(prompt):
    try:
        completion = client.chat.completions.create(
            # --- MUDANÇA AQUI: Modelo atualizado para Llama 3.3 ---
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
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

# --- INICIALIZAÇÃO ---
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Perfil (Groq 3.3)")
    st.metric("Nível", st.session_state.nivel)
    st.progress(st.session_state.xp / 100 if st.session_state.xp < 100 else 1.0)
    if st.button("🔄 Reiniciar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("⚡ LinguistAI Ultra-Rápido")

if st.button("✨ Gerar Nova Lição"):
    with st.spinner("Gerando instantaneamente..."):
        prompt = (f"Gere uma frase em inglês nível {st.session_state.nivel} para estudo. "
                  f"Responda EXATAMENTE neste formato: Phrase: [Frase em Inglês] | Translation: [Tradução Português]")
        
        # Chama a função corrigida
        res = chamar_ia(prompt)
        
        if "Phrase:" in res:
            st.session_state.aula_atual = res
            st.session_state.xp += 20
        else:
            st.error("A IA respondeu fora do formato. Tente de novo.")

if 'aula_atual' in st.session_state and st.session_state.aula_atual:
    st.markdown("---")
    try:
        texto = st.session_state.aula_atual
        # Tratamento de erro caso a IA mude um pouco o formato
        if "|" in texto:
            ing = texto.split("|")[0].split("Phrase:")[-1].strip()
            pt = texto.split("|")[1].split("Translation:")[-1].strip()
            
            st.subheader("Traduza:")
            st.info(pt)
            
            if st.button("🔊 Ver Resposta e Ouvir"):
                st.success(ing)
                play_audio(ing)
        else:
            st.warning("Formato inesperado: " + texto)
    except Exception as e:
        st.error(f"Erro ao processar: {e}")

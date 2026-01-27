import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# --- CONFIGURAÇÃO DA IA ---
# Busca a chave nos Secrets do Streamlit Cloud de forma segura
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Usamos o 1.5-flash por ser mais rápido e ter maior cota gratuita
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("Erro: Configure a chave 'GOOGLE_API_KEY' nos Secrets do Streamlit.")
except Exception as e:
    st.error(f"Erro de inicialização: {e}")

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Ocorreu um erro ao gerar o áudio.")

# --- GERENCIAMENTO DE ESTADO ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    if 'obj' in st.session_state:
        st.write(f"**Objetivo:** {st.session_state.obj}")
        st.write(f"**XP Total:** {st.session_state.xp}")
        # Barra de progresso visual
        progresso = min(st.session_state.xp / 100, 1.0)
        st.progress(progresso)
    if st.button("Reiniciar Aplicativo"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- TELAS DO APLICATIVO ---

# TELA 1: ESCOLHA DE OBJETIVO
if st.session_state.step == 'setup':
    st.title("🎧 LinguistAI")
    st.subheader("Seu treinador de inglês com IA")
    
    obj = st.selectbox("Qual seu foco de estudo hoje?", 
                        ["Trabalho (Business)", "Viagens (Travel)", "Conversação Social"])
    
    if st.button("Confirmar e Começar"):
        st.session_state.obj = obj
        st.session_state.step = 'practice'
        st.rerun()

# TELA 2: ÁREA DE TREINAMENTO
elif st.session_state.step == 'practice':
    st.title("🏋️ Área de Treinamento")
    st.write(f"Treinando para: **{st.session_state.obj}**")
    
    if st.button("✨ Gerar Nova Lição"):
        with st.spinner("A IA está criando sua lição..."):
            try:
                # Prompt otimizado para o modelo Flash
                prompt = (f"Create 1 short English sentence for {st.session_state.obj}. "
                          f"Format exactly: Phrase: [English] | Translation: [Portuguese]")
                
                response = model.generate_content(prompt)
                st.session_state.aula_atual = response.text
                st.session_state.xp += 10
            except Exception as e:
                # Sistema de Plano B (Fallback) caso a cota do Google acabe
                st.warning("Cota da IA atingida temporariamente. Usando lição de reserva...")
                st.session_state.aula_atual = "Phrase: Could you please help me with this? | Translation: Você poderia me ajudar com isso?"

    # EXIBIÇÃO DA LIÇÃO
    if 'aula_atual' in st.session_state:
        st.markdown("---")
        try:
            texto = st.session_state.aula_atual
            if "|" in texto:
                partes = texto.split("|")
                ingles = partes[0].replace("Phrase:", "").strip()
                portugues = partes[1].replace("Translation:", "").strip()
                
                st.subheader("Como se diz em Inglês?")
                st.info(portugues)
                
                if st.button("🔊 Ouvir Pronúncia"):
                    play_audio(ingles)
                    st.success(f"Correto: {ingles}")
                    st.toast("+10 XP Ganho! 🔥")
            else:
                st.write(texto) # Exibe o texto bruto se a formatação falhar
        except:
            st.error("Erro ao processar a lição. Tente gerar uma nova.")

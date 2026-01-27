import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import random

# --- CONFIGURAÇÃO ---
def setup_model():
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = setup_model()

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio temporariamente indisponível.")

# --- ESTADO DO APP ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'nivel' not in st.session_state: st.session_state.nivel = 'A1'
if 'xp' not in st.session_state: st.session_state.xp = 0

# --- SIDEBAR COM BARRA DE PROGRESSO ---
with st.sidebar:
    st.title("👤 Seu Perfil")
    st.metric("Nível Atual", st.session_state.nivel)
    
    # Lógica de Nível: a cada 100 XP você sobe de nível
    xp_proximo_nivel = 100
    progresso_calc = (st.session_state.xp % xp_proximo_nivel) / xp_proximo_nivel
    
    st.write(f"**XP Total:** {st.session_state.xp}")
    st.progress(progresso_calc)
    st.caption(f"Faltam {xp_proximo_nivel - (st.session_state.xp % xp_proximo_nivel)} XP para o próximo nível!")

    if st.button("🔄 Reiniciar App"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- FLUXO DE TELAS ---

# TELA 1: CONFIGURAÇÃO
if st.session_state.step == 'setup':
    st.title("🚀 LinguistAI")
    obj = st.selectbox("O que você quer praticar?", ["Business", "Travel", "Social"])
    if st.button("Iniciar Teste de Nivelamento"):
        st.session_state.obj = obj
        with st.spinner("IA preparando desafio..."):
            try:
                res = model.generate_content("Generate 1 short B1 level English sentence. Return ONLY the sentence.")
                st.session_state.frase_teste = res.text.strip()
            except:
                st.session_state.frase_teste = "Technology is changing the way we work every day."
            st.session_state.step = 'test'
            st.rerun()

# TELA 2: TESTE DE NÍVEL (VALIDAÇÃO REAL)
elif st.session_state.step == 'test':
    st.title("🎤 Teste de Nível")
    st.write("Escreva o que você ouviu (ou a tradução):")
    play_audio(st.session_state.frase_teste)
    
    res_user = st.text_input("Sua resposta:", key="input_teste")
    
    if st.button("Avaliar meu Nível"):
        if res_user:
            with st.spinner("Analisando..."):
                try:
                    prompt = f"Correct: '{st.session_state.frase_teste}'. User: '{res_user}'. Is it correct? Answer YES or NO and give CEFR level."
                    aval = model.generate_content(prompt).text.upper()
                    
                    if "NO" in aval and len(res_user) < 4:
                        st.error("❌ Resposta incorreta! Tente ouvir novamente com atenção.")
                    else:
                        for n in ["A1", "A2", "B1", "B2", "C1"]:
                            if n in aval: st.session_state.nivel = n
                        st.success(f"Nível detectado: {st.session_state.nivel}")
                        st.session_state.step = 'practice'
                        st.rerun()
                except:
                    st.session_state.nivel = "B1"
                    st.session_state.step = 'practice'
                    st.rerun()
        else:
            st.warning("Você precisa escrever algo para continuar!")

# TELA 3: ÁREA DE TREINO
elif st.session_state.step == 'practice':
    st.title("🏋️ Treinamento")
    st.info(f"Foco: {st.session_state.obj} | Nível: {st.session_state.nivel}")

    if st.button("✨ Próxima Frase"):
        with st.spinner("IA gerando frase única..."):
            try:
                seed = random.randint(1, 2000)
                prompt = f"English sentence level {st.session_state.nivel} for {st.session_state.obj}. Seed {seed}. Format: Phrase: [English] | Translation: [Portuguese]"
                st.session_state.aula_atual = model.generate_content(prompt).text
                # Ganha XP ao gerar e praticar
                st.session_state.xp += 20
                st.toast("+20 XP! 🔥")
            except:
                st.error("Erro na IA. Aguarde 10 segundos.")

    if 'aula_atual' in st.session_state:
        st.markdown("---")
        if "|" in st.session_state.aula_atual:
            p = st.session_state.aula_atual.split("|")
            ingles = p[0].replace("Phrase:", "").strip()
            portugues = p[1].replace("Translation:", "").strip()
            
            st.subheader("Tradução:")
            st.write(f"💡 *{portugues}*")
            if st.button("🔊 Ver Resposta e Ouvir"):
                play_audio(ingles)
                st.success(f"**Inglês:** {ingles}")

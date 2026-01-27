import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

DIFICULDADES = {
    "Begginer": "Frases ultra simples (2-3 palavras).",
    "basic": "Frases simples no presente.",
    "intermediate": "Passado, futuro e conectores.",
    "advanced": "Expressões idiomáticas e phrasal verbs.",
    "professional": "Inglês corporativo e formal.",
    "fluenty": "Nível nativo, gírias e nuances complexas."
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 2. FUNÇÕES DE APOIO ---

def chamar_ia(prompt, temp=0.7):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return completion.choices[0].message.content
    except: return "Erro na conexão."

def transcrever_audio(audio_bytes):
    try:
        res = client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3-turbo", response_format="text")
        return res
    except: return None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except: st.warning("Áudio indisponível.")

# --- 3. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'modo' not in st.session_state: st.session_state.modo = 'pratica'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'test_streak' not in st.session_state: st.session_state.test_streak = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None
if 'texto_falado' not in st.session_state: st.session_state.texto_falado = None

# --- 4. INTERFACE ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Configuração Inicial")
    st.session_state.nivel = st.selectbox("Em qual nível você quer praticar?", LISTA_NIVEIS)
    st.session_state.obj_selecionado = st.selectbox("Seu foco:", ["Social", "Business", "Travel"])
    if st.button("Iniciar ➡️"):
        st.session_state.step = 'app'
        st.rerun()

elif st.session_state.step == 'app':
    with st.sidebar:
        st.title("🕹️ Modos de Jogo")
        if st.button("📖 Prática Diária", use_container_width=True):
            st.session_state.modo = 'pratica'
            st.session_state.aula_atual = None
            st.rerun()
            
        if st.button("🏆 Teste de Nível", use_container_width=True):
            st.session_state.modo = 'teste'
            st.session_state.test_streak = 0
            st.session_state.aula_atual = None
            st.rerun()
            
        st.divider()
        st.write(f"Nível: **{st.session_state.nivel}**")
        if st.session_state.modo == 'teste':
            st.warning(f"Streak do Teste: {st.session_state.test_streak}/5")
            st.progress(st.session_state.test_streak / 5)
        else:
            st.success("Modo Prática Ativo")

    # CONTEÚDO DINÂMICO
    if st.session_state.modo == 'pratica':
        st.title("📖 Prática Livre")
        st.info("Treine sem pressão. Seus erros aqui não resetam seu progresso.")
    else:
        st.title("🏆 Teste de Maestria")
        st.warning("Atenção: Você precisa de 5 acertos seguidos. Se errar, volta para a Prática!")

    # GERADOR DE PERGUNTA
    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        st.session_state.aula_atual = None
        st.session_state.feedback = None
        st.session_state.texto_falado = None
        
        prompt = (f"Gere uma frase em inglês nível {st.session_state.nivel}. "
                  f"Dificuldade: {DIFICULDADES[st.session_state.nivel]} "
                  f"Contexto: {st.session_state.obj_selecionado}. "
                  f"Responda: Phrase: [Inglês] | Translation: [Português]")
        
        res = chamar_ia(prompt)
        if "|" in res:
            st.session_state.aula_atual = res
            st.session_state.mic_key += 1
            st.rerun()

    # ÁREA DA LIÇÃO
    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.markdown(f"### Como você diz:\n> **{pt}**")
            if st.button("🔊 Ouvir Resposta"): play_audio(ing)

            st.write("---")
            audio = mic_recorder(start_prompt="🎤 Gravar", stop_prompt="⏹️ Analisar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("IA analisando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno disse '{fala}' para '{ing}'. Dê feedback. Se estiver certo diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        
                        if "CORRETO" in st.session_state.feedback.upper():
                            if st.session_state.modo == 'teste':
                                st.session_state.test_streak += 1
                                if st.session_state.test_streak >= 5:
                                    st.balloons()
                                    idx = LISTA_NIVEIS.index(st.session_state.nivel)
                                    if idx < len(LISTA_NIVEIS)-1:
                                        st.session_state.nivel = LISTA_NIVEIS[idx+1]
                                        st.session_state.modo = 'pratica'
                                        st.success(f"🔥 NÍVEL UP! Você agora está no nível {st.session_state.nivel}!")
                            else:
                                st.success("Mandou bem!")
                        else:
                            if st.session_state.modo == 'teste':
                                st.error("❌ Erro no teste! Você foi redirecionado para a Prática.")
                                st.session_state.modo = 'pratica'
                                st.session_state.test_streak = 0

            if st.session_state.feedback:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                st.write(f"📝 **Feedback:** {st.session_state.feedback}")
                st.write(f"✅ **Gabarito:** {ing}")
        except Exception as e:
            st.error("Erro ao carregar desafio. Clique em Próxima Pergunta.")

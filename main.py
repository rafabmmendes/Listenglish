import streamlit as st
from groq import Groq
from gtts import gTTS
from io import BytesIO
import random
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA API ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Erro na API Key. Verifique os Secrets.")

# --- 2. MAPEAMENTO DE DIFICULDADE ---
# Esta tabela regula como a IA vai se comportar em cada nível
DIFICULDADES = {
    "Begginer": {"instrucao": "Use frases de 1 a 3 palavras. Ex: 'Good morning', 'I am fine'.", "temp": 0.5},
    "basic": {"instrucao": "Frases simples no presente. Sujeito + Verbo + Predicado. Ex: 'I like to play'.", "temp": 0.6},
    "intermediate": {"instrucao": "Use passado simples e futuro. Inclua conjunções como 'but', 'so', 'because'.", "temp": 0.7},
    "advanced": {"instrucao": "Use Phrasal Verbs e Present Perfect. Frases com mais de 10 palavras.", "temp": 0.8},
    "professional": {"instrucao": "Vocabulário de escritório, negócios e negociação. Termos formais.", "temp": 0.9},
    "fluenty": {"instrucao": "Frases nativas, gírias complexas, metáforas e gramática avançada de nível C2.", "temp": 1.0}
}
LISTA_NIVEIS = list(DIFICULDADES.keys())

# --- 3. FUNÇÕES AUXILIARES ---

def chamar_ia(prompt, temperatura=0.7):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro: {e}"

def transcrever_audio(audio_bytes):
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3-turbo", 
            response_format="text"
        )
        return transcription
    except:
        return None

def play_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp.getvalue(), format="audio/mp3")
    except:
        st.warning("Áudio indisponível.")

# --- 4. ESTADO DA SESSÃO ---
if 'step' not in st.session_state: st.session_state.step = 'objetivo'
if 'nivel' not in st.session_state: st.session_state.nivel = 'Begginer'
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'aula_atual' not in st.session_state: st.session_state.aula_atual = None
if 'mic_key' not in st.session_state: st.session_state.mic_key = 0
if 'feedback' not in st.session_state: st.session_state.feedback = None

# --- 5. INTERFACE DO APP ---

if st.session_state.step == 'objetivo':
    st.title("🎯 Definir Objetivo")
    obj = st.selectbox("O que você quer focar?", ["Social Conversations", "Business", "Travel", "Job Interview"])
    if st.button("Configurar Dificuldade ➡️"):
        st.session_state.obj_selecionado = obj
        st.session_state.step = 'teste_nivel'
        st.rerun()

elif st.session_state.step == 'teste_nivel':
    st.title("📝 Teste de Dificuldade")
    p = st.radio("Como se diz 'A maçã é vermelha'?", ["The apple is red", "The red is apple"])
    if st.button("Finalizar"):
        st.session_state.nivel = "basic" if p == "The apple is red" else "Begginer"
        st.session_state.step = 'pratica'
        st.rerun()

elif st.session_state.step == 'pratica':
    # SIDEBAR COM STATUS
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        st.metric("Nível Atual", st.session_state.nivel)
        
        # Barra de Dificuldade Visual
        idx_progresso = LISTA_NIVEIS.index(st.session_state.nivel) + 1
        st.write(f"Dificuldade da IA: **{idx_progresso}/6**")
        st.progress(idx_progresso / 6)
        
        st.write(f"XP para o próximo nível: {st.session_state.xp}/100")
        if st.button("🔄 Reiniciar Curso"):
            st.session_state.step = 'objetivo'
            st.rerun()

    st.title("🎙️ Prática Regulada por IA")
    
    # GERADOR DE PERGUNTA INFINITA
    if st.button("⏭️ Próxima Pergunta", type="primary") or st.session_state.aula_atual is None:
        with st.spinner("IA ajustando dificuldade..."):
            st.session_state.aula_atual = None
            st.session_state.feedback = None
            
            config = DIFICULDADES[st.session_state.nivel]
            seed = random.randint(1, 10000)
            
            prompt = (f"Seed:{seed}. Você é um professor de inglês. "
                      f"Dificuldade: {st.session_state.nivel}. "
                      f"Instrução técnica: {config['instrucao']}. "
                      f"Contexto: {st.session_state.obj_selecionado}. "
                      f"Responda apenas: Phrase: [Inglês] | Translation: [Português]")
            
            res = chamar_ia(prompt, temperatura=config['temp'])
            if "|" in res:
                st.session_state.aula_atual = res
                st.session_state.mic_key += 1
                st.rerun()

    # ÁREA DE EXIBIÇÃO
    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            ing = texto.split("|")[0].split("Phrase:")[-1].replace("[","").replace("]","").strip()
            pt = texto.split("|")[1].split("Translation:")[-1].replace("[","").replace("]","").strip()
            
            st.subheader(f"Dificuldade Atual: {st.session_state.nivel}")
            st.info(f"**Traduza:** {pt}")
            
            if st.button("🔊 Ouvir Referência"):
                play_audio(ing)

            # MICROFONE
            audio = mic_recorder(start_prompt="🎤 Gravar", stop_prompt="⏹️ Parar", key=f"mic_{st.session_state.mic_key}")

            if audio:
                with st.spinner("Analisando..."):
                    fala = transcrever_audio(audio['bytes'])
                    if fala:
                        st.session_state.texto_falado = fala
                        p_corr = f"O aluno disse '{fala}' para '{ing}'. Corrija brevemente. Se estiver certo diga CORRETO."
                        st.session_state.feedback = chamar_ia(p_corr)
                        if "CORRETO" in st.session_state.feedback.upper():
                            st.session_state.xp += 25

            if st.session_state.feedback:
                st.write(f"🗣️ **Você disse:** {st.session_state.texto_falado}")
                st.write(f"📝 **Feedback:** {st.session_state.feedback}")
                st.write(f"✅ **Gabarito:** {ing}")
                
            # SUBIR DE NÍVEL (DIFICULTAR)
            if st.session_state.xp >= 100:
                st.balloons()
                st.session_state.xp = 0
                idx = LISTA_NIVEIS.index(st.session_state.nivel)
                if idx < len(LISTA_NIVEIS) - 1:
                    st.session_state.nivel = LISTA_NIVEIS[idx + 1]
                    st.success(f"Dificuldade aumentada para: {st.session_state.nivel}!")

        except Exception as e:
            st.error("Erro ao gerar desafio. Clique em Próxima.")

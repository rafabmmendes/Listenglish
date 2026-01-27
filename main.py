# BOTÃO PRÓXIMA (COM RE-TENTATIVA AUTOMÁTICA)
    if st.button("⏭️ Próxima Pergunta", type="primary"):
        with st.spinner("Gerando novo desafio..."):
            # Prompt mais rígido para evitar erros de formato
            prompt = (f"Gere uma frase curta em inglês nível {st.session_state.nivel} sobre {st.session_state.obj_selecionado}. "
                      f"Responda APENAS no formato: Phrase: [inglês] | Translation: [português]. "
                      f"Não adicione saudações ou explicações.")
            
            res = chamar_ia(prompt)
            
            # Validação: verifica se a IA enviou o símbolo "|"
            if "|" in res and "Phrase:" in res:
                st.session_state.aula_atual = res
                st.session_state.feedback = None
                st.session_state.texto_falado = None
                st.session_state.mic_key += 1
                st.rerun()
            else:
                st.error("A IA falhou no formato. A tentar novamente...")
                # Tenta uma segunda vez automaticamente com um prompt de emergência
                res_retry = chamar_ia("Gere uma frase simples. Formato: Phrase: Dog | Translation: Cão")
                st.session_state.aula_atual = res_retry
                st.rerun()

    # EXIBIÇÃO DA LIÇÃO (MAIS RESISTENTE A ERROS)
    if st.session_state.aula_atual:
        try:
            texto = st.session_state.aula_atual
            # Limpeza de caracteres extras que a IA possa ter enviado
            partes = texto.split("|")
            ing = partes[0].replace("Phrase:", "").replace("[", "").replace("]", "").strip()
            pt = partes[1].replace("Translation:", "").replace("[", "").replace("]", "").strip()
            
            st.info(f"**Traduza:** {pt}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔊 Ouvir"):
                    play_audio(ing)

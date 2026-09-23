import streamlit as st
from openai import OpenAI
import tempfile
import os
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Inicializa o cliente da OpenAI utilizando a chave guardada nos Secrets seguros do Streamlit
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="Easy REDS",
    layout="wide"
)

st.markdown("""
# 📋 Easy REDS
""")

# Inicializa os estados de sessão para acumular texto e fotos
if "relato_acumulado" not in st.session_state:
    st.session_state.relato_acumulado = ""

if "lista_fotos" not in st.session_state:
    st.session_state.lista_fotos = []

# Função para gerar PDF formatado
def gerar_pdf(conteudo_texto):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor='black'
    )
    
    story = []
    linhas = conteudo_texto.split('\n')
    for linha in linhas:
        if linha.strip():
            if linha.startswith("###") or linha.startswith("##") or linha.startswith("#"):
                p = Paragraph(f"<b>{linha.replace('#', '').strip()}</b>", style_normal)
            else:
                p = Paragraph(linha, style_normal)
            story.append(p)
            story.append(Spacer(1, 6))
            
    doc.build(story)
    return temp_pdf.name

col1, col2 = st.columns(2)

with col1:
    # Seletor de Natureza
    natureza_ocorrencia = st.selectbox(
        "Selecione a Natureza:",
        [
            "Acidente de Trânsito com Vítima / Capotamento / Atropelamento",
            "Incêndio em Edificação / Vegetação / Veículo",
            "Salvamento e Resgate (Altura, Água, Confinado)",
            "Busca e Salvamento de Desaparecidos",
            "Atendimento Pré-Hospitalar (Clínico/Trauma Geral)",
            "Outras Ocorrências / Defesa Civil"
        ]
    )
    
    st.subheader("Dados (Cena / Retorno)")
    
    # Recurso de Gravação Direta por Microfone
    st.markdown("🎙️")
    audio_bytes = st.audio_input("Grave o relato da ocorrência falando ao microfone:")
    
    if audio_bytes is not None:
        audio_hash = hash(audio_bytes.getvalue())
        if "ultimo_audio" not in st.session_state or st.session_state.ultimo_audio != audio_hash:
            st.session_state.ultimo_audio = audio_hash
            with st.spinner("A transcrever áudio do microfone..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(audio_bytes.read())
                        tmp_path = tmp.name
                    
                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f
                        )
                    novo_texto = transcript.text
                    
                    if st.session_state.relato_acumulado.strip():
                        st.session_state.relato_acumulado += f"\n{novo_texto}"
                    else:
                        st.session_state.relato_acumulado = novo_texto
                        
                    st.success("Áudio transcrito e adicionado ao relato com sucesso!")
                    os.unlink(tmp_path)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na transcrição por microfone: {e}")

    relato_bruto = st.text_area(
        "Relato Bruto da Guarnição / Equipe:",
        value=st.session_state.relato_acumulado,
        height=220,
        placeholder="Ex: Equipe empenhada em acidente de trânsito na via..."
    )
    
    st.session_state.relato_acumulado = relato_bruto
    
    if st.button("Limpar Relato Bruto"):
        st.session_state.relato_acumulado = ""
        st.rerun()

    st.markdown("---")
    
    # Estilo compacto estilo WhatsApp para anexos (Grampo e Câmara lado a lado)
    st.markdown("📎 **Adicionar Evidências e Documentos:**")
    col_grampo, col_cam = st.columns(2)
    
    with col_grampo:
        fich_carregados = st.file_uploader("📁 Carregar Ficheiros", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="up_multiplos")
        if fich_carregados:
            if st.button("Confirmar Ficheiros"):
                for f in fich_carregados:
                    st.session_state.lista_fotos.append({
                        "bytes": f.read(),
                        "type": f.type if f.type else "image/jpeg",
                        "nome": f.name
                    })
                st.success(f"{len(fich_carregados)} ficheiro(s) adicionado(s)!")
                st.rerun()

    with col_cam:
        foto_capturada = st.camera_input("📷 Tirar Foto (Câmara)")
        if foto_capturada is not None:
            foto_hash = hash(foto_capturada.getvalue())
            if "ultima_foto_hash" not in st.session_state or st.session_state.ultima_foto_hash != foto_hash:
                st.session_state.ultima_foto_hash = foto_hash
                st.session_state.lista_fotos.append({
                    "bytes": foto_capturada.getvalue(),
                    "type": "image/jpeg",
                    "nome": f"Foto_Camera_{len(st.session_state.lista_fotos)+1}.jpg"
                })
                st.success("Foto da câmara adicionada!")
                st.rerun()

    # Exibição compacta das evidências em formato de lista lateral (lado a lado) com opção de expansão
    if st.session_state.lista_fotos:
        st.markdown(f"**Evidências anexadas ({len(st.session_state.lista_fotos)}):** Click para expandir")
        
        # Cria grelha lado a lado para ocupar pouco espaço vertical
        cols_Grelha = st.columns(min(len(st.session_state.lista_fotos), 3))
        for idx, item in enumerate(st.session_state.lista_fotos):
            with cols_Grelha[idx % 3]:
                # Usa expander para a imagem ficar oculta/limpa e só abrir se o utilizador clicar
                with st.expander(f"📄 {item['nome']} (Ver)"):
                    st.image(item["bytes"], use_container_width=True)
                    if st.button("❌ Remover", key=f"rem_{idx}"):
                        st.session_state.lista_fotos.pop(idx)
                        st.rerun()
        
        if st.button("🗑️ Limpar Todas as Evidências"):
            st.session_state.lista_fotos = []
            if "ultima_foto_hash" in st.session_state:
                del st.session_state.ultima_foto_hash
            st.rerun()

    st.markdown("---")
    processar = st.button("Processar, Ler Documentos e Auditar Ocorrência", type="primary", use_container_width=True)

with col2:
    st.subheader("Minuta:")
    
    if processar:
        if not relato_bruto.strip() and not st.session_state.lista_fotos:
            st.warning("⚠️ Validação Pré-auditoria: Insira um relato de texto/voz ou adicione ao menos uma foto/documento para prosseguir.")
        else:
            SYSTEM_INSTRUCTION_REDS = f"""
            Você é o Assistente Técnico Especialista em Registros Operacionais e Auditoria de Ocorrências do CBMMG.
            A natureza operacional selecionada para esta ocorrência é: {natureza_ocorrencia}.

            DIRETRIZES TÉCNICAS E JURÍDICAS MANDATÓRIAS:
            1. FIDELIDADE FACTUAL ESTATUÁRIA: O documento normativo diz o que deve ser feito; o histórico registra o que foi REALMENTE feito. Não presuma procedimentos, técnicas ou dados clínicos não informados.
            2. VEDAÇÃO A TERMOS GENÉRICOS: Nunca utilize expressões vagas como "procedimentos de praxe", "cuidados pertinentes" ou "conforme protocolo". Descreva a conduta real ou limite-se aos fatos citados.
            3. RELATO DE TERCEIRO VS. CONSTATAÇÃO DA EQUIPE: Toda dinâmica de acidente, perda de controle ou autoria não testemunhada diretamente pela guarnição/equipe DEVE ser atribuída formalmente ao declarante.
            4. CONCISÃO E ECONOMIA DE DADOS NO HISTÓRICO: Evite poluir o texto com números de placas, prefixos e matrículas que já possuem campos específicos no sistema.
            5. VEDAÇÃO A DIAGNÓSTICO MÉDICO: Descreva apenas achados e queixas anatômicas/visíveis, jamais ateste diagnósticos patológicos fechados.
            6. LEITURA DE DOCUMENTOS E IMAGENS MÚLTIPLAS: Se forem enviadas várias imagens de documentos (RGs, CPFs, CNHs de diferentes envolvidos) ou cenas, extraia rigorosamente todos os dados textuais visíveis em cada uma delas para compor os campos estruturados de forma detalhada.

            FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):
            ### BLOCO A: CAMPOS ESTRUTURADOS (Extraia com precisão cirúrgica os dados de nomes, CPFs, RGs, idades e veículos vindos do texto e de todas as imagens enviadas)
            ### BLOCO B: HISTÓRICO NARRATIVO COMPLETO (Redigido com clareza técnica militar e impessoalidade)
            ### BLOCO C: AUDITORIA TÉCNICA E PENDÊNCIAS (Apontando riscos de glosa, inconsistências e dados faltantes críticos)
            """

            with st.spinner(f"A analisar todas as evidências e auditar ocorrência ({natureza_ocorrencia})..."):
                try:
                    conteudo_mensagem = [{"type": "text", "text": f"DADOS DA OCORRÊNCIA E RELATO:\n{relato_bruto}"}]
                    
                    for foto in st.session_state.lista_fotos:
                        encoded_img = base64.b64encode(foto["bytes"]).decode("utf-8")
                        conteudo_mensagem.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{foto['type']};base64,{encoded_img}"
                            }
                        })
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_INSTRUCTION_REDS},
                            {"role": "user", "content": conteudo_mensagem}
                        ],
                        temperature=0.1
                    )
                    
                    resultado = response.choices[0].message.content
                    st.markdown(resultado)
                    
                    st.markdown("---")
                    pdf_path = gerar_pdf(resultado)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Descarregar Relatório Oficial em PDF",
                            data=f,
                            file_name="Minuta_Auditoria_REDS.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"Erro no processamento da IA: {e}")

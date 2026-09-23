import streamlit as st
from openai import OpenAI
import tempfile
import os
import base64
import urllib.parse
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

# Inicializa os estados de sessão para garantir persistência
if "relato_acumulado" not in st.session_state:
    st.session_state.relato_acumulado = ""

if "lista_fotos" not in st.session_state:
    st.session_state.lista_fotos = []

if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = ""

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
            "Salvamento (Altura, Aquático, Terrestre)",
            "Busca e Salvamento de Desaparecidos",
            "Atendimento Pré-Hospitalar (Clínico/Trauma Geral)",
            "Outras Ocorrências / Defesa Civil"
        ]
    )
    
    st.subheader("Dados (Cena / Retorno)")
    
    # Sistema de Gravação de Áudio com Diagnóstico de Erro Detalhado
    st.markdown("🎙️")
    audio_bytes = st.audio_input("Grave o relato da ocorrência falando ao microfone:")
    
    if audio_bytes is not None:
        audio_hash = hash(audio_bytes.getvalue())
        if "ultimo_audio" not in st.session_state or st.session_state.ultimo_audio != audio_hash:
            st.session_state.ultimo_audio = audio_hash
            with st.spinner("A transcrever áudio do microfone..."):
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(audio_bytes.read())
                        tmp_path = tmp.name
                    
                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f,
                            language="pt"
                        )
                    novo_texto = transcript.text
                    
                    if novo_texto and novo_texto.strip():
                        if st.session_state.relato_acumulado.strip():
                            st.session_state.relato_acumulado += f"\n{novo_texto}"
                        else:
                            st.session_state.relato_acumulado = novo_texto
                            
                        st.success("Áudio transcrito e adicionado ao relato com sucesso!")
                    else:
                        st.warning("⚠️ O áudio foi gravado, mas a transcrição veio vazia.")
                        
                    os.unlink(tmp_path)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro detalhado na transcrição Whisper: {str(e)}")
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)

    # Callback para manter o texto sincronizado no session_state em tempo real
    def atualizar_relato():
        st.session_state.relato_acumulado = st.session_state.input_relato_texto

    relato_bruto = st.text_area(
        "Relato Bruto da Guarnição / Equipe:",
        value=st.session_state.relato_acumulado,
        height=220,
        placeholder="Ex: Equipe empenhada em acidente de trânsito na via...",
        key="input_relato_texto",
        on_change=atualizar_relato
    )
    
    st.session_state.relato_acumulado = relato_bruto

    if st.button("Limpar Relato Bruto"):
        st.session_state.relato_acumulado = ""
        st.session_state.lista_fotos = []
        st.session_state.ultimo_resultado = ""
        if "ultimo_audio" in st.session_state:
            del st.session_state.ultimo_audio
        st.rerun()

    st.markdown("---")
    
    # Sistema de Documentos robusto
    st.markdown("📎 **Documentos:**")
    fich_carregados = st.file_uploader(
        "Abrir arquivo:", 
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
        key="upload_geral_completo"
    )
    
    if fich_carregados:
        if st.button("Adicionar Evidências Selecionadas"):
            try:
                for f in fich_carregados:
                    conteudo_bytes = f.read()
                    tipo_mime = f.type if f.type else "image/jpeg"
                    
                    ja_existe = any(item["nome"] == f.name and len(item["bytes"]) == len(conteudo_bytes) for item in st.session_state.lista_fotos)
                    if not ja_existe:
                        st.session_state.lista_fotos.append({
                            "bytes": conteudo_bytes,
                            "type": tipo_mime,
                            "nome": f.name
                        })
                st.success("Evidência(s) adicionada(s) com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao carregar ficheiro: {str(e)}")

    # Exibição limpa em formato de lista expansível
    if st.session_state.lista_fotos:
        st.markdown(f"**Evidências prontas para envio ({len(st.session_state.lista_fotos)}):**")
        
        for idx, item in enumerate(st.session_state.lista_fotos):
            with st.expander(f"📄 {item['nome']} (Ver imagem)"):
                try:
                    st.image(item["bytes"], use_container_width=True)
                except:
                    st.info("Ficheiro carregado (pré-visualização gráfica indisponível para este formato).")
                
                if st.button("❌ Remover", key=f"rem_{idx}"):
                    st.session_state.lista_fotos.pop(idx)
                    st.rerun()
        
        if st.button("🗑️ Limpar Todas as Evidências"):
            st.session_state.lista_fotos = []
            st.rerun()

    st.markdown("---")
    processar = st.button("Gerar Relatório", type="primary", use_container_width=True)

with col2:
    st.subheader("Relatório:")
    
    if processar:
        if not relato_bruto.strip() and not st.session_state.lista_fotos:
            st.warning("⚠️ Validação: Insira um relato de texto/voz ou adicione ao menos uma foto/documento para prosseguir.")
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
            6. LEITURA OBRIGATÓRIA DE DOCUMENTOS E IMAGENS: Analise com máxima atenção todas as imagens de documentos (RGs, CPFs, CNHs) ou fotos de cena enviadas. Extraia rigorosamente todos os dados textuais visíveis nelas (nomes completos, números de documentos, datas de nascimento, filiação, etc.) para preencher os campos do Bloco A com precisão absoluta.

            FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):
            ### BLOCO A: CAMPOS ESTRUTURADOS (Extraia com precisão cirúrgica todos os dados de nomes, CPFs, RGs, idades e veículos vindos do texto e de todas as imagens enviadas)
            ### BLOCO B: HISTÓRICO NARRATIVO COMPLETO (Redigido com clareza técnica militar e impessoalidade)
            ### BLOCO C: AUDITORIA TÉCNICA И PENDÊNCIAS (Apontando riscos de glosa, inconsistências e dados faltantes críticos)
            """

            with st.spinner(f"A ler documentos, analisar evidências e gerar relatório ({natureza_ocorrencia})..."):
                try:
                    conteudo_mensagem = [{"type": "text", "text": f"DADOS DA OCORRÊNCIA E RELATO:\n{relato_bruto}\n\nPor favor, analise rigorosamente todas as imagens/documentos anexados abaixo para extração de dados:"}]
                    
                    for foto in st.session_state.lista_fotos:
                        encoded_img = base64.b64encode(foto["bytes"]).decode("utf-8")
                        mime = foto["type"] if foto["type"] else "image/jpeg"
                        conteudo_mensagem.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{encoded_img}"
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
                    st.session_state.ultimo_resultado = resultado
                    
                except Exception as e:
                    st.error(f"❌ Erro detalhado na API da OpenAI (GPT-4o-mini): {str(e)}")

    # Exibe o resultado e as opções de partilha mantendo o estado na sessão
    if st.session_state.ultimo_resultado:
        st.markdown(st.session_state.ultimo_resultado)
        
        st.markdown("---")
        st.subheader("📤 Exportação e Partilha:")
        
        pdf_path = gerar_pdf(st.session_state.ultimo_resultado)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        col_pdf, col_wapp, col_mail = st.columns(3)
        
        with col_pdf:
            st.download_button(
                label="📥 Baixar PDF",
                data=pdf_bytes,
                file_name="Relatorio_Auditoria_REDS.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_wapp:
            texto_wapp = urllib.parse.quote(f"*RELATÓRIO DE REDS - EASY REDS*\n\n{st.session_state.ultimo_resultado}")
            url_whatsapp = f"https://api.whatsapp.com/send?text={texto_wapp}"
            st.markdown(
                f'<a href="{url_whatsapp}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">🟢 WhatsApp</button></a>',
                unsafe_allow_html=True
            )
            
        with col_mail:
            assunto_mail = urllib.parse.quote("Relatório de Ocorrência - Easy REDS")
            corpo_mail = urllib.parse.quote(st.session_state.ultimo_resultado)
            url_email = f"mailto:?subject={assunto_mail}&body={corpo_mail}"
            st.markdown(
                f'<a href="{url_email}" target="_blank"><button style="width:100%; background-color:#0078D4; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">📧 E-mail</button></a>',
                unsafe_allow_html=True
            )

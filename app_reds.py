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
    page_title="Assistente de Confeção e Auditoria de Registros Operacionais",
    layout="wide"
)

st.markdown("""
# 📋 Assistente Avançado de Confeção e Auditoria de Registros Operacionais
*Motor de Inteligência Artificial com Visão Computacional, Transcrição de Voz e Conformidade Doutrinária*
""")

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

# Seleção Dinâmica da Natureza da Ocorrência
natureza_ocorrencia = st.sidebar.selectbox(
    "Selecione a Natureza Principal:",
    [
        "Acidente de Trânsito com Vítima / Capotamento / Atropelamento",
        "Incêndio em Edificação / Vegetação / Veículo",
        "Salvamento e Resgate (Altura, Água, Confinado)",
        "Busca e Salvamento de Desaparecidos",
        "Atendimento Pré-Hospitalar (Clínico/Trauma Geral)",
        "Outras Ocorrências / Defesa Civil"
    ]
)

SYSTEM_INSTRUCTION_REDS = f"""
Você é o Assistente Técnico Especialista em Registros Operacionais e Auditoria de Ocorrências do CBMMG.
A natureza operacional selecionada para esta ocorrência é: {natureza_ocorrencia}.

DIRETRIZES TÉCNICAS E JURÍDICAS MANDATÓRIAS:
1. FIDELIDADE FACTUAL ESTATUÁRIA: O documento normativo diz o que deve ser feito; o histórico registra o que foi REALMENTE feito. Não presuma procedimentos, técnicas ou dados clínicos não informados.
2. VEDAÇÃO A TERMOS GENÉRICOS: Nunca utilize expressões vagas como "procedimentos de praxe", "cuidados pertinentes" ou "conforme protocolo". Descreva a conduta real ou limite-se aos fatos citados.
3. RELATO DE TERCEIRO VS. CONSTATAÇÃO DA EQUIPE: Toda dinâmica de acidente, perda de controle ou autoria não testemunhada diretamente pela guarnição/equipe DEVE ser atribuída formalmente ao declarante.
4. CONCISÃO E ECONOMIA DE DADOS NO HISTÓRICO: Evite poluir o texto com números de placas, prefixos e matrículas que já possuem campos específicos no sistema.
5. VEDAÇÃO A DIAGNÓSTICO MÉDICO: Descreva apenas achados e queixas anatômicas/visíveis, jamais ateste diagnósticos patológicos fechados.
6. LEITURA DE DOCUMENTOS E IMAGENS: Se forem enviadas imagens de documentos (RGs, CPFs, CNHs) ou cenas, extraia rigorosamente todos os dados textuais visíveis nelas para compor os campos estruturados.

FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):
### BLOCO A: CAMPOS ESTRUTURADOS (Extraia com precisão cirúrgica os dados de nomes, CPFs, RGs, idades e veículos vindos do texto e das imagens anexadas)
### BLOCO B: HISTÓRICO NARRATIVO COMPLETO (Redigido com clareza técnica militar e impessoalidade)
### BLOCO C: AUDITORIA TÉCNICA E PENDÊNCIAS (Apontando riscos de glosa, inconsistências e dados faltantes críticos)
"""

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Coleta Operacional (Cena / Retorno)")
    
    # Recurso de Gravação Direta por Microfone (Push-to-talk / Áudio Nativo)
    st.markdown("🎙️ **Gravação Direta de Voz (Microfone):**")
    audio_bytes = st.audio_input("Grave o relato da ocorrência falando ao microfone:")
    
    transcricao_voz = ""
    if audio_bytes is not None:
        with st.spinner("A transcrever áudio do microfone com inteligência artificial..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_bytes.read())
                    tmp_path = tmp.name
                
                with open(tmp_path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
                transcricao_voz = transcript.text
                st.success("Áudio transcrito e incorporado com sucesso!")
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"Erro na transcrição por microfone: {e}")

    # Combina texto digitado ou gerado por voz
    relato_bruto = st.text_area(
        "Relato Bruto da Guarnição / Equipe:",
        value=transcricao_voz if transcricao_voz else "",
        height=220,
        placeholder="Ex: Equipe empenhada em acidente de trânsito na via..."
    )
    
    # Upload de Imagens (Documentos, RGs, CPFs, Cenas)
    uploaded_file = st.file_uploader("Evidências Visuais e Documentos (RG, CPF, CNH, Fotos da Cena):", type=["jpg", "png", "jpeg"])
    
    processar = st.button("Processar, Ler Documentos e Auditar Ocorrência", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Minuta Estruturada e Auditoria Normativa")
    
    if processar:
        if not relato_bruto.strip() and not uploaded_file:
            st.warning("⚠️ Validação Pré-auditoria: Insira um relato de texto/voz ou envie uma imagem/documento para prosseguir.")
        else:
            with st.spinner(f"A analisar documentos e auditar ocorrência ({natureza_ocorrencia})..."):
                try:
                    # Monta o conteúdo multimodal (Texto + Imagem opcional)
                    conteudo_mensagem = [{"type": "text", "text": f"DADOS DA OCORRÊNCIA E RELATO:\n{relato_bruto}"}]
                    
                    if uploaded_file is not None:
                        image_bytes = uploaded_file.read()
                        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                        # Determina o tipo MIME correto baseado na extensão
                        mime_type = uploaded_file.type if uploaded_file.type else "image/jpeg"
                        
                        conteudo_mensagem.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}"
                            }
                        })
                    
                    # Chamada utilizando o modelo gpt-4o-mini com suporte a visão e texto
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
                    
                    # Botão de Exportação em PDF
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

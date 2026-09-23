import streamlit as st
from openai import OpenAI
import tempfile
import os
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
*Motor de Inteligência Artificial para Padronização Doutrinária, Análise de Conformidade e Transcrição*
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
    # Divide o texto em parágrafos para o PDF
    linhas = conteudo_texto.split('\n')
    for linha in linhas:
        if linha.strip():
            # Converte títulos simples em negrito/destaque
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

# Instruções dinâmicas baseadas na natureza escolhida
SYSTEM_INSTRUCTION_REDS = f"""
Você é o Assistente Técnico Especialista em Registros Operacionais e Auditoria de Ocorrências do CBMMG.
A natureza operacional selecionada para esta ocorrência é: {natureza_ocorrencia}.

DIRETRIZES TÉCNICAS E JURÍDICAS MANDATÓRIAS:
1. FIDELIDADE FACTUAL ESTATUÁRIA: O documento normativo diz o que deve ser feito; o histórico registra o que foi REALMENTE feito. Não presuma procedimentos, técnicas ou dados clínicos não informados.
2. VEDAÇÃO A TERMOS GENÉRICOS: Nunca utilize expressões vagas como "procedimentos de praxe", "cuidados pertinentes" ou "conforme protocolo". Descreva a conduta real ou limite-se aos fatos citados.
3. RELATO DE TERCEIRO VS. CONSTATAÇÃO DA EQUIPE: Toda dinâmica de acidente, perda de controle ou autoria não testemunhada diretamente pela guarnição/equipe DEVE ser atribuída formalmente ao declarante.
4. CONCISÃO E ECONOMIA DE DADOS NO HISTÓRICO: Evite poluir o texto com números de placas, prefixos e matrículas que já possuem campos específicos no sistema.
5. VEDAÇÃO A DIAGNÓSTICO MÉDICO: Descreva apenas achados e queixas anatômicas/visíveis, jamais ateste diagnósticos patológicos fechados.

FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):
### BLOCO A: CAMPOS ESTRUTURADOS (Extraia em formato de tabela ou lista limpa com Nomes, CPFs, RGs, Idades, Danos e Veículos envolvidos)
### BLOCO B: HISTÓRICO NARRATIVO COMPLETO (Redigido com clareza técnica militar e impessoalidade)
### BLOCO C: AUDITORIA TÉCNICA E PENDÊNCIAS (Apontando riscos de glosa, inconsistências e dados faltantes críticos)
"""

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Coleta Operacional (Cena / Retorno)")
    
    # Recurso de Transcrição por Voz (Whisper)
    st.markdown("🎙️ **Ditar Relato por Voz (Áudio):**")
    audio_file = st.file_uploader("Envie um áudio da guarnição (.mp3, .wav, .m4a, .ogg):", type=["mp3", "wav", "m4a", "ogg"])
    
    transcricao_gerada = ""
    if audio_file is not None:
        if st.button("Transcrever Áudio Automaticamente"):
            with st.spinner("A transcrever áudio com inteligência artificial..."):
                try:
                    # Salva temporariamente para enviar à API Whisper
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp:
                        tmp.write(audio_file.read())
                        tmp_path = tmp.name
                    
                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f
                        )
                    transcricao_gerada = transcript.text
                    st.success("Áudio transcrito com sucesso! O texto foi aplicado abaixo.")
                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"Erro na transcrição: {e}")

    # Caixa de texto combinando digitação direta ou texto transcrito
    texto_inicial = transcricao_gerada if transcricao_gerada else ""
    relato_bruto = st.text_area(
        "Relato Bruto da Guarnição / Equipe:",
        value=texto_inicial,
        height=230,
        placeholder="Ex: Equipe empenhada em acidente de trânsito na via..."
    )
    
    uploaded_file = st.file_uploader("Evidências Visuais (Fotos da Cena, Documentos, Veículos):", type=["jpg", "png", "jpeg"])
    
    processar = st.button("Processar, Validar e Auditar Ocorrência", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Minuta Estruturada e Auditoria Normativa")
    
    if processar:
        if not relato_bruto.strip():
            st.warning("⚠️ Validação Pré-auditoria: Por favor, insira ou transcreva o relato bruto da ocorrência para prosseguir.")
        else:
            # Validação básica de campos mínimos recomendados
            dados_alerta = []
            if len(relato_bruto) < 15:
                dados_alerta.endswith("O relato parece muito curto para uma ocorrência detalhada.")
                
            with st.spinner(f"A auditar e estruturar ({natureza_ocorrencia})..."):
                try:
                    # Chamada utilizando o modelo gpt-4o-mini
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_INSTRUCTION_REDS},
                            {"role": "user", "content": f"DADOS DA OCORRÊNCIA:\n{relato_bruto}"}
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

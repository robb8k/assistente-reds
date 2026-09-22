import os
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# Inicializa o cliente do Gemini utilizando a chave configurada
client = genai.Client()

SYSTEM_INSTRUCTION_REDS = """
Você é o Assistente Técnico Especialista em Registros Operacionais e Auditoria de Ocorrências, 
fundamentado nas normas institucionais vigentes (incluindo diretrizes de atendimento pré-hospitalar, salvamento, combate a incêndio e manuais operacionais aplicáveis).

DIRETRIZES TÉCNICAS E JURÍDICAS MANDATÓRIAS:
1. FIDELIDADE FACTUAL ESTATUÁRIA: O documento normativo diz o que deve ser feito; o histórico registra o que foi REALMENTE feito. Não presuma procedimentos, técnicas ou dados clínicos não informados.
2. VEDAÇÃO A TERMOS GENÉRICOS: Nunca utilize expressões vagas como "procedimentos de praxe", "cuidados pertinentes" ou "conforme protocolo". Descreva a conduta real ou limite-se aos fatos citados.
3. RELATO DE TERCEIRO VS. CONSTATAÇÃO DA EQUIPE: Toda dinâmica de acidente, perda de controle ou autoria não testemunhada diretamente pela guarnição/equipe DEVE ser atribuída formalmente ao declarante (ex: "Segundo relato do Envolvido 01, este transitava...").
4. CONCISÃO E ECONOMIA DE DADOS NO HISTÓRICO: Evite poluir o texto com números de placas, prefixos e matrículas que já possuem campos específicos na aba Recursos e Envolvidos. Concentre o histórico na atribuição das ações e repasses de responsabilidade.
5. VEDAÇÃO A DIAGNÓSTICO MÉDICO: Descreva apenas achados e queixas anatômicas/visíveis (ex: "escoriações na região frontal"), jamais ateste diagnósticos patológicos fechados.

FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):

### BLOCO A: CAMPOS ESTRUTURADOS (RED/REGISTRO)
- Natureza Principal (Código e Descrição oficial)
- Natureza Secundária / Suporte (se houver empenho de apoio especializado)
- Formulário de Registro correspondente
- Local do Fato
- Veículo(s) envolvido(s): Dados cadastrais e avarias visíveis
- Envolvido(s) / Vítima(s): Qualificação (Envolvido 01, 02...) com vínculo (condutor, passageiro, pedestre), idade e lesões relatadas
- Órgãos de Apoio: Órgão, guarnição e viatura
- Destinação/Repasse: Destino de vítimas e bens

### BLOCO B: HISTÓRICO NARRATIVO COMPLETO
[Texto redigido em ordem cronológica de 5 fases: Acionamento -> Situação encontrada -> Relato de terceiros/envolvidos -> Atuação da Equipe -> Desfecho e repasses. Estritamente impessoal, formal, conciso e sem redundâncias cadastrais.]

### BLOCO C: AUDITORIA TÉCNICA E PENDÊNCIAS
Classificação de Prontidão: [🟢 SEM PENDÊNCIAS] | [🟡 PENDÊNCIA DE ESCLARECIMENTO] | [🔴 INCONSISTÊNCIA DETECTADA]
- Checklist de lacunas: Apontar ausência de dados obrigatórios exigidos pelas normas técnicas (ex: dados hospitalares para relatórios de atendimento, situação da fiação/poste na colisão, ausência de técnicas operacionais caso citada vítima retida).
"""

st.set_page_config(page_title="Assistente de Registros Operacionais", page_icon="📋", layout="wide")

st.title("📋 Assistente de Confecção e Auditoria de Registros Operacionais")
st.caption("Motor de Inteligência Artificial para Padronização Doutrinária e Análise de Conformidade")

col_input, col_output = st.columns([1, 1])

with col_input:
    st.subheader("1. Coleta Operacional (Cena / Retorno)")
    
    relato_texto = st.text_area(
        "Relato Bruto da Guarnição / Equipe (digite ou cole a transcrição do áudio):",
        height=180,
        placeholder="Ex: Acidente de carro contra poste na Getúlio Vargas. Condutor Alzemar escoriações na cabeça, levado pra UPA. Apoio policial no local..."
    )
    
    arquivos_imagens = st.file_uploader(
        "Evidências Visuais (Documentos, Cenas, Veículos, Apoio):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    botao_processar = st.button("🚀 Processar e Auditar Ocorrência", type="primary", use_container_width=True)

with col_output:
    st.subheader("2. Minuta Estruturada e Auditoria Normativa")
    
    if botao_processar:
        if not relato_texto and not arquivos_imagens:
            st.warning("⚠️ Insira ao menos um relato em texto ou uma imagem para processamento.")
        else:
            with st.spinner("Analisando evidências, consultando padrões normativos e auditando o histórico..."):
                try:
                    conteudos_envio = []
                    
                    if arquivos_imagens:
                        for arq in arquivos_imagens:
                            img = Image.open(arq)
                            conteudos_envio.append(img)
                    
                    if relato_texto:
                        conteudos_envio.append(f"DADOS COLETADOS PELA EQUIPE:\n{relato_texto}")
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=conteudos_envio,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION_REDS,
                            temperature=0.1
                        )
                    )
                    
                    resultado = response.text
                    st.markdown(resultado)
                    
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")
import streamlit as st
from openai import OpenAI

# Inicializa o cliente da OpenAI utilizando a chave guardada nos Secrets seguros do Streamlit
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="Assistente de Confeção e Auditoria de Registros Operacionais",
    layout="wide"
)

st.markdown("""
# 📋 Assistente de Confeção e Auditoria de Registros Operacionais
*Motor de Inteligência Artificial para Padronização Doutrinária e Análise de Conformidade*
""")

# Instrução de Sistema (Mantendo rigorosamente a doutrina do CBMMG)
SYSTEM_INSTRUCTION_REDS = """
Você é o Assistente Técnico Especialista em Registros Operacionais e Auditoria de Ocorrências, 
fundamentado nas normas institucionais vigentes do CBMMG.

DIRETRIZES TÉCNICAS E JURÍDICAS MANDATÓRIAS:
1. FIDELIDADE FACTUAL ESTATUÁRIA: O documento normativo diz o que deve ser feito; o histórico registra o que foi REALMENTE feito. Não presuma procedimentos, técnicas ou dados clínicos não informados.
2. VEDAÇÃO A TERMOS GENÉRICOS: Nunca utilize expressões vagas como "procedimentos de praxe", "cuidados pertinentes" ou "conforme protocolo". Descreva a conduta real ou limite-se aos fatos citados.
3. RELATO DE TERCEIRO VS. CONSTATAÇÃO DA EQUIPE: Toda dinâmica de acidente, perda de controle ou autoria não testemunhada diretamente pela guarnição/equipe DEVE ser atribuída formalmente ao declarante.
4. CONCISÃO E ECONOMIA DE DADOS NO HISTÓRICO: Evite poluir o texto com números de placas, prefixos e matrículas que já possuem campos específicos.
5. VEDAÇÃO A DIAGNÓSTICO MÉDICO: Descreva apenas achados e queixas anatômicas/visíveis, jamais ateste diagnósticos patológicos fechados.

FORMATO ESTRITO DE RESPOSTA (DIVIDIDO EM 3 BLOCOS):
### BLOCO A: CAMPOS ESTRUTURADOS
### BLOCO B: HISTÓRICO NARRATIVO COMPLETO
### BLOCO C: AUDITORIA TÉCNICA E PENDÊNCIAS
"""

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Coleta Operacional (Cena / Retorno)")
    relato_bruto = st.text_area(
        "Relato Bruto da Guarnição / Equipe (digite ou cole a transcrição do áudio):",
        height=250,
        placeholder="Ex: Equipe empenhada em acidente de trânsito..."
    )
    
    uploaded_file = st.file_uploader("Evidências Visuais (Documentos, Cenas, Veículos, Apoio):", type=["jpg", "png", "jpeg"])
    
    processar = st.button("Processar e Auditar Ocorrência", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Minuta Estruturada e Auditoria Normativa")
    
    if processar:
        if not relato_bruto.strip():
            st.warning("Por favor, insira o relato bruto da ocorrência para prosseguir.")
        else:
            with st.spinner("A processar e auditar ocorrência com o motor OpenAI (gpt-4o-mini)..."):
                try:
                    # Chamada direta e estável utilizando o modelo gpt-4o-mini
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
                    
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")

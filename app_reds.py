import streamlit as st
import google.generativeai as genai
import time

# Configura a chave da API do Gemini usando os Secrets do Streamlit
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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
### BLOCO C: AUDITORIA TÉCNICA И PENDÊNCIAS
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
            with st.spinner("A processar e auditar ocorrência com o motor Gemini..."):
                sucesso = False
                tentativas = 3
                
                # Sistema de tentativas automáticas para contornar oscilações de rede ou alta demanda
                for tentativa in range(tentativas):
                    try:
                        # Utiliza o modelo atualizado e nativo do Gemini
                        model = genai.GenerativeModel(
                            model_name="gemini-2.0-flash",
                            system_instruction=SYSTEM_INSTRUCTION_REDS
                        )
                        
                        response = model.generate_content(
                            f"DADOS DA OCORRÊNCIA:\n{relato_bruto}"
                        )
                        
                        st.markdown(response.text)
                        sucesso = True
                        break
                        
                    except Exception as e:
                        if ("503" in str(e) or "404" in str(e)) and tentativa < tentativas - 1:
                            time.sleep(2) # Espera 2 segundos antes de tentar novamente
                            continue
                        else:
                            st.error(f"Erro no processamento: {e}")
                            sucesso = True
                            break

import streamlit as st
import sqlite3
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Configuração da página do Streamlit
st.set_page_config(page_title="Mix Auto Peças - IA", page_icon="🚗", layout="centered")

st.title("🚗 Mix Auto Peças - Assistente de Estoque Inteligente")
st.markdown("Faça perguntas sobre peças, preços e aplicações utilizando linguagem natural.")

# Função de busca SQL no banco de 20k SKUs
def consultar_estoque(nome_peca="", modelo_carro=""):
    conn = sqlite3.connect("estoque_mix.db")
    cursor = conn.cursor()
    
    query = "SELECT id, nome, aplicacao, quantidade, preco FROM pecas WHERE 1=1"
    params = []
    
    if nome_peca:
        query += " AND nome LIKE ?"
        params.append(f"%{nome_peca}%")
        
    if modelo_carro and modelo_carro.strip():
        query += " AND aplicacao LIKE ?"
        params.append(f"%{modelo_carro}%")
        
    query += " LIMIT 10"
    
    cursor.execute(query, params)
    linhas = cursor.fetchall()
    conn.close()
    
    resultados = []
    for linha in linhas:
        resultados.append({
            "id": linha[0],
            "nome": linha[1],
            "aplicacao": linha[2],
            "quantidade": linha[3],
            "preco": linha[4]
        })
        
    return json.dumps(resultados) if resultados else json.dumps({"aviso": "Nenhuma peça encontrada com esses critérios."})

# Ferramentas da IA
# Ferramentas da IA (Ajustadas para nunca recusar buscas genéricas)
ferramentas = [
    {
        "type": "function",
        "function": {
            "name": "consultar_estoque",
            "description": "Busca peças no inventário de 20 mil SKUs. Se o usuário digitar apenas o nome da peça (ex: Junta), busque imediatamente usando apenas o nome_peca e deixe modelo_carro vazio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_peca": {
                        "type": "string",
                        "description": "O nome ou tipo da peça (ex: Junta, Pastilha, Vela)."
                    },
                    "modelo_carro": {
                        "type": "string",
                        "description": "O modelo do veículo. Deixe totalmente em branco se o usuário não citar nenhum carro."
                    }
                },
                # Removemos a exigência estrita para dar liberdade total à IA
                "required": []
            }
        }
    }
]

# Inicializa o histórico de mensagens do chat na tela
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Exibe o histórico de mensagens anteriores
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# Entrada do usuário na caixa de chat do Streamlit
if prompt_usuario := st.chat_input("Ex: Tem peça pro Palio? / Mostra as juntas"):
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # Processamento da IA e Tool Calling
    with st.chat_message("assistant"):
        with st.spinner("Consultando estoque..."):
            try:
                # 1. Envia a mensagem para a IA
                resposta_ia = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.mensagens],
                    tools=ferramentas
                )
                
                mensagem_retorno = resposta_ia.choices[0].message
                
                # 2. Se a IA chamou a ferramenta de banco de dados
                if mensagem_retorno.tool_calls:
                    chamada = mensagem_retorno.tool_calls[0]
                    argumentos = json.loads(chamada.function.arguments)
                    
                    # Executa a query SQL
                    resultado_banco = consultar_estoque(**argumentos)
                    
                    # 3. Devolve o resultado para a IA formular a resposta final
                    segunda_resposta = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {"role": "user", "content": prompt_usuario},
                            mensagem_retorno,
                            {
                                "role": "tool",
                                "tool_call_id": chamada.id,
                                "content": resultado_banco
                            }
                        ]
                    )
                    resposta_final = segunda_resposta.choices[0].message.content
                else:
                    resposta_final = mensagem_retorno.content

                st.markdown(resposta_final)
                # Adiciona a resposta do assistente ao histórico
                st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a solicitação: {e}")
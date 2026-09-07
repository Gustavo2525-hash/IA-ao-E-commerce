import sqlite3
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 1. Inicializa o cliente e carrega a chave do .env
load_dotenv()
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# 2. A Função de Consulta SQL Real (Conectada ao banco de 20 mil SKUs)
def consultar_estoque(nome_peca="", modelo_carro=""):
    """Consulta o banco SQLite filtrando por nome e/ou aplicação de forma otimizada."""
    conn = sqlite3.connect("estoque_mix.db")
    cursor = conn.cursor()
    
    # Monta a query dinamicamente baseada nos parâmetros enviados pela IA
    query = "SELECT id, nome, aplicacao, quantidade, preco FROM pecas WHERE 1=1"
    params = []
    
    if nome_peca:
        query += " AND nome LIKE ?"
        params.append(f"%{nome_peca}%")
        
    if modelo_carro:
        query += " AND aplicacao LIKE ?"
        params.append(f"%{modelo_carro}%")
        
    # Limita a 10 resultados para a IA não se afogar em dados caso a busca seja ampla
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

# 3. A 'Tool' que ensina a IA como buscar no nosso sistema
ferramentas = [
    {
        "type": "function",
        "function": {
            "name": "consultar_estoque",
            "description": "Busca peças no inventário de 20 mil SKUs da loja. Use os parâmetros para filtrar a busca.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_peca": {
                        "type": "string",
                        "description": "O nome, tipo ou categoria da peça (ex: Junta, Pastilha, Bomba, Vela)."
                    },
                    "modelo_carro": {
                        "type": "string",
                        "description": "O modelo do veículo (ex: Palio, Civic, Corolla, Gol). Pode ficar vazio se não informado."
                    }
                },
                "required": ["nome_peca"]
            }
        }
    }
]

# 4. O Fluxo de Atendimento Principal
def atender_vendedor(mensagem_vendedor):
    print(f"👤 Vendedor: {mensagem_vendedor}")
    
    # Passo A: Envia a pergunta para a IA junto com as ferramentas disponíveis
    resposta_ia = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": mensagem_vendedor}],
        tools=ferramentas
    )
    
    mensagem_retorno = resposta_ia.choices[0].message
    
    # Passo B: Verifica se a IA decidiu que precisa consultar o estoque
    if mensagem_retorno.tool_calls:
        chamada = mensagem_retorno.tool_calls[0]
        argumentos = json.loads(chamada.function.arguments)
        
        print(f"⚙️ [Backend SQLite] Filtros aplicados pela IA: {argumentos}")
        
        # Executa a função SQL real desempacotando os parâmetros
        resultado_banco = consultar_estoque(**argumentos)
        
        # Passo C: Devolve os dados do banco para a IA formular a resposta final
        resposta_final = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": mensagem_vendedor},
                mensagem_retorno,
                {
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": resultado_banco
                }
            ]
        )
        print(f"🤖 Assistente: {resposta_final.choices[0].message.content}\n")

# 5. Simulando o uso no balcão da loja com buscas complexas
print("--- Teste de Integração Mix Auto Peças (Banco SQLite 20k SKUs) ---\n")
atender_vendedor("Opa, tem alguma peça pro Palio ai no estoque?")
atender_vendedor("Cliente tá perguntando de peça pro Civic. Tem? Qual o preço?")
atender_vendedor("Mostra quais juntas a gente tem no estoque aí, por favor.")
atender_vendedor("Me lista aí todas as velas de ignição que a gente tem para o Corolla, quero saber preço e estoque.")
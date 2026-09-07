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

# 2. Nosso Banco de Dados Mockado (Estoque Mix Auto Peças)
estoque_mix = [
    {"id": 1, "nome": "Pastilha de Freio Cobreq", "aplicacao": "Palio", "quantidade": 4, "preco": 89.90},
    {"id": 2, "nome": "Filtro de Óleo Fram", "aplicacao": "Civic", "quantidade": 0, "preco": 45.50},
    {"id": 3, "nome": "Bomba D'água Urba", "aplicacao": "Gol", "quantidade": 2, "preco": 150.00}
]

# 3. A Função Python que simula a Query SQL
def consultar_estoque(modelo_carro):
    """Busca peças disponíveis no banco de dados filtrando pelo modelo do veículo."""
    resultados = [peca for peca in estoque_mix if modelo_carro.lower() in peca['aplicacao'].lower()]
    return json.dumps(resultados) if resultados else json.dumps({"aviso": "Nenhuma peça encontrada para este modelo."})

# 4. A 'Tool' que ensina a IA como buscar no nosso sistema
ferramentas = [
    {
        "type": "function",
        "function": {
            "name": "consultar_estoque",
            "description": "Verifica o estoque e os preços das peças automotivas por modelo de carro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "modelo_carro": {
                        "type": "string",
                        "description": "O modelo do carro extraído da mensagem (ex: Palio, Civic, Gol)."
                    }
                },
                "required": ["modelo_carro"]
            }
        }
    }
]

# 5. O Fluxo de Atendimento Principal
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
        
        print(f"⚙️ [Backend] A IA solicitou busca no banco para o carro: {argumentos['modelo_carro']}")
        
        # Executa a função Python real com os parâmetros da IA
        resultado_banco = consultar_estoque(argumentos['modelo_carro'])
        
        # Passo C: Devolve os dados brutos do sistema para a IA formular a resposta final humanizada
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

# Simulando o uso no balcão da loja
print("--- Teste de Integração Mix Auto Peças ---\n")
atender_vendedor("Opa, tem alguma peça pro Palio ai no estoque?")
atender_vendedor("Cliente tá perguntando de peça pro Civic. Tem? Qual o preço?")
import sqlite3
import random

# Conecta ao banco de dados SQLite (ele cria o arquivo automaticamente)
conn = sqlite3.connect("estoque_mix.db")
cursor = conn.cursor()

# Cria a tabela de peças com índice otimizado para busca
cursor.execute("""
CREATE TABLE IF NOT EXISTS pecas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    aplicacao TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco REAL NOT NULL
)
""")

# Listas base para gerar variação realista de autopeças
tipos_pecas = [
    "Pastilha de Freio", "Filtro de Óleo", "Bomba D'água", "Amortecedor Dianteiro", 
    "Correia Dentada", "Vela de Ignição", "Disco de Freio", "Junta do Cabeçote", 
    "Alternador", "Kit de Embreagem", "Radiador", "Farol Principal", "Bateria 60Ah"
]
marcas = ["Cobreq", "Fram", "Urba", "Nakata", "Bosch", "NGK", "Fremax", "Taranto", "Sabó", "Valeo"]
carros = ["Palio", "Civic", "Gol", "Corolla", "Onix", "HB20", "Strada", "Hilux", "Ka", "Sandero"]

print("Gerando e inserindo 20.000 peças no banco SQLite...")

# Gerador em massa simulando 20 mil itens
massa_dados = []
for i in range(1, 20001):
    peca = random.choice(tipos_pecas)
    marca = random.choice(marcas)
    nome_completo = f"{peca} {marca}"
    aplicacao = random.choice(carros)
    quantidade = random.randint(0, 15)  # De 0 a 15 unidades em estoque
    preco = round(random.uniform(25.0, 850.0), 2)
    
    massa_dados.append((nome_completo, aplicacao, quantidade, preco))

# Insere tudo de uma vez usando transação em lote (performance máxima)
cursor.executemany("""
INSERT INTO pecas (nome, aplicacao, quantidade, preco)
VALUES (?, ?, ?, ?)
""", massa_dados)

conn.commit()
conn.close()
print("Banco de dados SQLite populado com sucesso com 20.000 SKUs!")


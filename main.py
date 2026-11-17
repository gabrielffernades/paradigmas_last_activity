import math
import sqlite3


#paradigma declarativo

VENDAS = [
    {"id": 1, "produto": "Mouse", "categoria": "Periféricos", "qtd": 3, "unitario": 80.0},
    {"id": 2, "produto": "Teclado", "categoria": "Periféricos", "qtd": 2, "unitario": 150.0},
    {"id": 3, "produto": "Monitor", "categoria": "Telas", "qtd": 1, "unitario": 900.0},
    {"id": 4, "produto": "Mouse", "categoria": "Periféricos", "qtd": 5, "unitario": 80.0},
    {"id": 5, "produto": "Notebook", "categoria": "Computadores", "qtd": 2, "unitario": 3500.0},
    {"id": 6, "produto": "Monitor", "categoria": "Telas", "qtd": 2, "unitario": 900.0},
    {"id": 7, "produto": "Cabo", "categoria": "Acessórios", "qtd": 4, "unitario": 35.0},
]

SCHEMA = """
CREATE TABLE vendas (
    id INTEGER PRIMARY KEY,
    produto TEXT NOT NULL,
    categoria TEXT NOT NULL,
    qtd INTEGER NOT NULL,
    unitario REAL NOT NULL
)
"""

SQL_RESUMO = """
SELECT
    COALESCE(SUM(qtd * unitario), 0) AS faturamento_total,
    COUNT(*) AS numero_registros,
    CASE
        WHEN COUNT(*) = 0 THEN 0
        ELSE SUM(qtd * unitario) / COUNT(*)
    END AS ticket_medio
FROM vendas
"""

SQL_POR_CATEGORIA = """
SELECT
    categoria,
    SUM(qtd * unitario) AS faturamento
FROM vendas
GROUP BY categoria
ORDER BY categoria
"""

SQL_POR_PRODUTO = """
SELECT
    produto,
    SUM(qtd) AS quantidade
FROM vendas
GROUP BY produto
ORDER BY produto
"""


# Percorre a lista e acumula total, média e agrupamentos no laço.
def calcular_procedural(vendas):
    total_geral = 0.0
    valor_por_categoria = {}
    quantidade_por_produto = {}
    numero_registros = 0

    for venda in vendas:
        subtotal = venda["qtd"] * venda["unitario"]
        total_geral += subtotal
        numero_registros += 1

        categoria = venda["categoria"]
        if categoria not in valor_por_categoria:
            valor_por_categoria[categoria] = 0.0
        valor_por_categoria[categoria] += subtotal

        produto = venda["produto"]
        if produto not in quantidade_por_produto:
            quantidade_por_produto[produto] = 0
        quantidade_por_produto[produto] += venda["qtd"]

    return {
        "faturamento_total": total_geral,
        "numero_registros": numero_registros,
        "ticket_medio": total_geral / numero_registros,
        "valor_por_categoria": valor_por_categoria,
        "quantidade_por_produto": quantidade_por_produto,
    }


# Grava as vendas numa tabela e obtém o relatório com consultas SQL.
def calcular_sql(vendas):
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    conexao.execute(SCHEMA)
    conexao.executemany(
        """
        INSERT INTO vendas (id, produto, categoria, qtd, unitario)
        VALUES (:id, :produto, :categoria, :qtd, :unitario)
        """,
        vendas,
    )

    resumo = conexao.execute(SQL_RESUMO).fetchone()
    categorias = conexao.execute(SQL_POR_CATEGORIA).fetchall()
    produtos = conexao.execute(SQL_POR_PRODUTO).fetchall()
    conexao.close()

    return {
        "faturamento_total": resumo["faturamento_total"],
        "numero_registros": resumo["numero_registros"],
        "ticket_medio": resumo["ticket_medio"],
        "valor_por_categoria": {
            linha["categoria"]: linha["faturamento"] for linha in categorias
        },
        "quantidade_por_produto": {
            linha["produto"]: linha["quantidade"] for linha in produtos
        },
    }


# Mostra o faturamento, o ticket médio e os agrupamentos.
def imprimir(relatorio):
    print("=== RELATÓRIO DE VENDAS ===")
    print(f"Faturamento total: R$ {relatorio['faturamento_total']:.2f}")
    print(f"Ticket médio por registro: R$ {relatorio['ticket_medio']:.2f}")

    print("\nFaturamento por categoria:")
    for categoria, valor in sorted(relatorio["valor_por_categoria"].items()):
        print(f"- {categoria}: R$ {valor:.2f}")

    print("\nQuantidade por produto:")
    for produto, quantidade in sorted(relatorio["quantidade_por_produto"].items()):
        print(f"- {produto}: {quantidade}")


# Compara o resultado SQL com o resultado do laço.
def conferir(obtido, esperado):
    divergencias = []

    if obtido["numero_registros"] != esperado["numero_registros"]:
        divergencias.append(
            f"numero_registros: SQL={obtido['numero_registros']} "
            f"procedural={esperado['numero_registros']}"
        )

    for campo in ("faturamento_total", "ticket_medio"):
        if not math.isclose(obtido[campo], esperado[campo], rel_tol=0.0, abs_tol=1e-9):
            divergencias.append(
                f"{campo}: SQL={obtido[campo]} procedural={esperado[campo]}"
            )

    for campo in ("valor_por_categoria", "quantidade_por_produto"):
        if obtido[campo].keys() != esperado[campo].keys():
            divergencias.append(f"{campo}: chaves diferentes")
            continue
        for chave, valor_esperado in esperado[campo].items():
            if not math.isclose(obtido[campo][chave], valor_esperado, rel_tol=0.0, abs_tol=1e-9):
                divergencias.append(
                    f"{campo}[{chave}]: SQL={obtido[campo][chave]} "
                    f"procedural={valor_esperado}"
                )

    return divergencias


# Executa os dois cálculos, imprime o relatório e confere se batem.
def main():
    esperado = calcular_procedural(VENDAS)
    obtido = calcular_sql(VENDAS)

    imprimir(obtido)

    print("\n=== CONFERÊNCIA ===")
    divergencias = conferir(obtido, esperado)
    if divergencias:
        print("As consultas SQL divergiram do código procedural:")
        for item in divergencias:
            print(f"- {item}")
        raise SystemExit(1)

    print("Consultas SQL equivalentes ao código procedural.")
    print(f"Registros conferidos: {obtido['numero_registros']}")
    print(f"Categorias: {len(obtido['valor_por_categoria'])}")
    print(f"Produtos: {len(obtido['quantidade_por_produto'])}")


if __name__ == "__main__":
    main()

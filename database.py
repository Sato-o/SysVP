import sqlite3
import csv
import os
from datetime import datetime

cliente_em_edicao = None

def conectar():
    return sqlite3.connect("fiados.db")

def criar_banco():
    conn = conectar()
    cur = conn.cursor()

    # Tabela de clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            telefone TEXT,
            endereco TEXT,
            observacao TEXT
        )
    """)

    # Tabela de produtos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            preco REAL
        )
    """)

    # Tabela de pedidos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            data_pagamento TEXT,
            valor_pago REAL DEFAULT 0,
            observacao TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)

    # Tabela de itens_pedido com ID exclusivo
    cur.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL DEFAULT 0,
            subtotal REAL,
            observacao TEXT DEFAULT '',
            FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        data TEXT,
        valor REAL,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
    )
    """)

    # Adiciona forma_pagamento se ainda não existir
    cur.execute("PRAGMA table_info(pagamentos)")
    colunas_pagamentos = [col[1] for col in cur.fetchall()]
    if "forma_pagamento" not in colunas_pagamentos:
        cur.execute("ALTER TABLE pagamentos ADD COLUMN forma_pagamento TEXT DEFAULT ''")

    # Verificações de colunas existentes
    cur.execute("PRAGMA table_info(itens_pedido)")
    colunas_itens = [col[1] for col in cur.fetchall()]
    
    # Segurança adicional: garantir preco_unitario e observacao
    if "preco_unitario" not in colunas_itens:
        cur.execute("ALTER TABLE itens_pedido ADD COLUMN preco_unitario REAL DEFAULT 0")
    if "observacao" not in colunas_itens:
        cur.execute("ALTER TABLE itens_pedido ADD COLUMN observacao TEXT DEFAULT ''")

    # Verificação para garantir que a coluna id existe
    if "id" not in colunas_itens:
        print("⚠️ Atenção: o banco de dados atual não possui a coluna 'id' em itens_pedido. Isso pode causar erros no salvamento.")

    cur.execute("PRAGMA table_info(pedidos)")
    colunas_pedidos = [col[1] for col in cur.fetchall()]
    if "valor_pago" not in colunas_pedidos:
        cur.execute("ALTER TABLE pedidos ADD COLUMN valor_pago REAL DEFAULT 0")
    if "observacao" not in colunas_pedidos:
        cur.execute("ALTER TABLE pedidos ADD COLUMN observacao TEXT DEFAULT ''")

    conn.commit()
    conn.close()

def salvar_ou_atualizar_cliente(nome, telefone, obs):
    global cliente_em_edicao
    conn = conectar()
    cur = conn.cursor()
    if cliente_em_edicao:
        cur.execute("UPDATE clientes SET nome=?, telefone=?, observacao=? WHERE id=?",
                    (nome, telefone, obs, cliente_em_edicao))
        cliente_em_edicao = None
    else:
        cur.execute("INSERT INTO clientes (nome, telefone, observacao) VALUES (?, ?, ?)",
                    (nome, telefone, obs))
    conn.commit()
    conn.close()

def editar_cliente_id(cid):
    global cliente_em_edicao
    cliente_em_edicao = cid

def listar_clientes():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, telefone, observacao FROM clientes")
    dados = cur.fetchall()
    conn.close()
    return dados

def listar_clientes_id():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM clientes")
    dados = cur.fetchall()
    conn.close()
    return dados

def excluir_cliente(id_cliente):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    conn.commit()
    conn.close()

def inserir_produto(nome, preco):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT nome, preco FROM produtos")
    dados = cur.fetchall()
    conn.close()
    return dados

def listar_produtos_detalhes():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, preco FROM produtos")
    dados = cur.fetchall()
    conn.close()
    return dados

def excluir_produto(produto_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM itens_pedido WHERE produto_id=?", (produto_id,))
    if cur.fetchone()[0] == 0:
        cur.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
    conn.commit()
    conn.close()

def registrar_pedido(cliente_id, data, produtos, observacao=""):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO pedidos (cliente_id, data, valor_pago, observacao) VALUES (?, ?, 0, ?)",
        (cliente_id, data, observacao)
    )

    pedido_id = cur.lastrowid

    for produto_id, quantidade, subtotal, observacao_item in produtos:
        preco_unitario = subtotal / quantidade if quantidade else 0
        cur.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, subtotal, observacao) VALUES (?, ?, ?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario, subtotal, observacao_item)
        )

    conn.commit()
    conn.close()

def excluir_pedido(pedido_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM itens_pedido WHERE pedido_id=?", (pedido_id,))
    cur.execute("DELETE FROM pedidos WHERE id=?", (pedido_id,))
    conn.commit()
    conn.close()

def marcar_pedido_como_pago(pedido_id):
    conn = conectar()
    cur = conn.cursor()
    data = datetime.now().strftime('%Y-%m-%d')
    cur.execute("UPDATE pedidos SET data_pagamento = ? WHERE id = ?", (data, pedido_id))
    conn.commit()
    conn.close()

def listar_pedidos_detalhados():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            c.nome AS cliente,
            p.nome AS produto,
            i.quantidade,
            d.data,
            (i.subtotal / i.quantidade) AS preco_unitario,
            i.subtotal,
            d.valor_pago,
            d.id AS pedido_id,
            d.observacao,
            i.produto_id,
            (SELECT SUM(subtotal) FROM itens_pedido WHERE pedido_id = d.id) AS total_pedido,
            i.id AS item_id,
            (
                SELECT forma_pagamento
                FROM pagamentos
                WHERE pedido_id = d.id
                ORDER BY data DESC
                LIMIT 1
            ) AS forma_pagamento
        FROM itens_pedido i
        JOIN pedidos d ON i.pedido_id = d.id
        JOIN produtos p ON i.produto_id = p.id
        JOIN clientes c ON d.cliente_id = c.id
    """)
    dados = cur.fetchall()
    conn.close()
    return dados

def listar_pedidos_por_cliente(cliente_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            d.data, 
            d.data_pagamento, 
            p.nome, 
            i.quantidade, 
            i.preco_unitario, 
            i.subtotal, 
            d.valor_pago, 
            d.id AS pedido_id, 
            d.observacao,
            (SELECT SUM(subtotal) FROM itens_pedido WHERE pedido_id = d.id) AS total_pedido,
            i.id AS item_id
        FROM pedidos d
        JOIN itens_pedido i ON d.id = i.pedido_id
        JOIN produtos p ON i.produto_id = p.id
        WHERE d.cliente_id = ?
    """, (cliente_id,))
    dados = cur.fetchall()
    conn.close()
    return dados


def obter_nome_e_totais_cliente(cliente_id):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.nome, 
               SUM(p.valor_pago), 
               SUM(
                   (SELECT SUM(i.subtotal) FROM itens_pedido i WHERE i.pedido_id = p.id)
               )
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE p.cliente_id = ?
    """, (cliente_id,))
    
    resultado = cur.fetchone()

    if resultado is None:
        return "Cliente sem pedidos", 0, 0

    nome, total_pago, total_subtotal = resultado
    total_pago = total_pago or 0
    total_subtotal = total_subtotal or 0
    total_aberto = total_subtotal - total_pago

    return nome, total_pago, total_aberto

def gerar_planilha_resumo(caminho):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            c.nome,
            MAX(p.data_pagamento) AS ultima_data_pagamento,
            SUM(
                (SELECT SUM(i.subtotal) FROM itens_pedido i WHERE i.pedido_id = p.id)
            ) AS total_pedidos,
            SUM(p.valor_pago) AS total_pago
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        GROUP BY c.nome
    """)

    linhas = cur.fetchall()
    conn.close()

    dados = []
    for nome, ultima_data, total, pago in linhas:
        total = total or 0
        pago = pago or 0
        aberto = total - pago
        if aberto > 0.01:
            valor_fmt = f"{aberto:.2f}".replace(".", ",")
            data_fmt = datetime.strptime(ultima_data, "%Y-%m-%d").strftime("%d/%m/%Y") if ultima_data else "—"
            dados.append((nome, valor_fmt, data_fmt))

    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Cliente", "Total em Aberto", "Último Pagamento"])
        writer.writerows(dados)

def gerar_planilha_pagos(caminho):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.nome, SUM(p.valor_pago) AS total_pago
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        GROUP BY c.nome
        HAVING total_pago > 0
    """)
    dados = cur.fetchall()
    conn.close()

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Cliente", "Total Pago"])
        writer.writerows(dados)

def listar_recebimentos_por_data(data):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            c.nome, 
            p.data,
            p.valor,
            (SELECT SUM(i2.subtotal) FROM itens_pedido i2 WHERE i2.pedido_id = d.id) as total_pedido,
            p.forma_pagamento
        FROM pagamentos p
        JOIN pedidos d ON d.id = p.pedido_id
        JOIN clientes c ON c.id = d.cliente_id
        WHERE p.data = ?
    """, (data,))
    dados = cur.fetchall()
    conn.close()
    return dados

def atualizar_valor_pago(pedido_id, valor):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT SUM(subtotal) FROM itens_pedido WHERE pedido_id=?", (pedido_id,))
    total = cur.fetchone()[0]

    cur.execute("SELECT valor_pago FROM pedidos WHERE id=?", (pedido_id,))
    atual = cur.fetchone()[0] or 0

    novo_valor = atual + valor

    if novo_valor >= total:
        cur.execute("UPDATE pedidos SET valor_pago = ?, data_pagamento = DATE('now') WHERE id=?", (total, pedido_id))
    else:
        cur.execute("UPDATE pedidos SET valor_pago = ? WHERE id=?", (novo_valor, pedido_id))

    conn.commit()
    conn.close()

def registrar_pagamento_parcial(pedido_id, valor_recebido, forma_pagamento):
    conn = conectar()
    cur = conn.cursor()

    # Atualiza subtotais
    cur.execute("""
        UPDATE itens_pedido
        SET subtotal = quantidade * preco_unitario
        WHERE pedido_id = ?
    """, (pedido_id,))

    cur.execute("SELECT SUM(subtotal) FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))
    total = cur.fetchone()[0] or 0

    cur.execute("SELECT valor_pago FROM pedidos WHERE id = ?", (pedido_id,))
    atual = cur.fetchone()[0] or 0

    novo_valor = atual + valor_recebido

    if novo_valor >= total:
        cur.execute("""
            UPDATE pedidos
            SET valor_pago = ?, data_pagamento = DATE('now')
            WHERE id = ?
        """, (total, pedido_id))
    else:
        cur.execute("""
            UPDATE pedidos
            SET valor_pago = ?, data_pagamento = COALESCE(data_pagamento, DATE('now'))
            WHERE id = ?
        """, (novo_valor, pedido_id))

    cur.execute("""
        INSERT INTO pagamentos (pedido_id, data, valor, forma_pagamento)
        VALUES (?, DATE('now'), ?, ?)
    """, (pedido_id, valor_recebido, forma_pagamento))

    conn.commit()
    conn.close()

def listar_pagamentos_por_data(data):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.id,
            c.nome,
            p.data,
            p.valor,
            p.forma_pagamento
        FROM pagamentos p
        JOIN pedidos d ON d.id = p.pedido_id
        JOIN clientes c ON c.id = d.cliente_id
        WHERE p.data = ?
    """, (data,))
    dados = cur.fetchall()
    conn.close()
    return dados
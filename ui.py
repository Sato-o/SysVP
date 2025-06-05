from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QStackedWidget,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QInputDialog, QSizePolicy, QGridLayout, QHBoxLayout, QDateEdit,
    QMainWindow, QTextEdit, QSpinBox, QCalendarWidget, QCompleter, QFileDialog, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QDate
from database import *
from datetime import datetime
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QDoubleValidator, QColor, QTextCharFormat, QStandardItemModel, QStandardItem, QTextDocument, QPixmap
from PyQt5.QtPrintSupport import QPrinter
from configuracoes_empresa import TelaConfiguracoes, carregar_configuracoes
import unicodedata
from weasyprint import HTML
import json, os, sys, base64

CONFIG_PATH = "config.json"

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.setDuration(300)

    def setCurrentIndexAnimated(self, index):
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.setCurrentIndex(index)
        self.anim.setEndValue(self.geometry())
        self.anim.start()

class TelaInicial(QWidget):  
    def __init__(self, mudar_tela, abrir_configuracoes):
        super().__init__()

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        coluna_esquerda = QVBoxLayout()
        coluna_esquerda.setSpacing(15)

        # Carrega logo e nome da empresa
        logo = QLabel()
        nome = QLabel("Nome Empresa")
        subtitulo = QLabel("Detalhamento")

        nome.setStyleSheet("font-weight: bold; font-size: 14px;")
        subtitulo.setStyleSheet("font-size: 10px; color: #aaa;")

        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                nome.setText(config.get("nome_empresa", "Nome Empresa"))
                subtitulo.setText(config.get("detalhamento", "Detalhamento"))
                logo_path = config.get("logo_path", "")
                if os.path.exists(logo_path):
                    pixmap = QPixmap(logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    logo.setPixmap(pixmap)

        logo.setFixedSize(64, 64)
        logo.setStyleSheet("border-radius: 32px;")

        # Info empresa layout
        info_layout = QHBoxLayout()
        info_text_layout = QVBoxLayout()
        info_text_layout.addWidget(nome)
        info_text_layout.addWidget(subtitulo)

        info_layout.addWidget(logo)
        info_layout.addLayout(info_text_layout)
        info_layout.setSpacing(10)

        coluna_esquerda.addLayout(info_layout)

        # Botões do menu
        botoes_info = [
            ("👥 Clientes", lambda: mudar_tela(1)),
            ("🛒 Produtos", lambda: mudar_tela(2)),
            ("📄 Registrar Pedido", lambda: mudar_tela(3)),
            ("📄 Fichas", lambda: mudar_tela(4)),
            ("💰 Recebimentos", lambda: mudar_tela(5)),
            ("📊 Gerar Planilha", self.gerar_planilha)
        ]

        for texto, acao in botoes_info:
            btn = QPushButton(texto)
            btn.setFixedSize(250, 60)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.clicked.connect(acao)
            btn.setStyleSheet("font-size: 14px;")
            coluna_esquerda.addWidget(btn)

        coluna_esquerda.addStretch()
        layout_principal.addLayout(coluna_esquerda)

        # Botão de configurações no canto inferior direito
        btn_config = QPushButton("\u2699")
        btn_config.setFixedSize(40, 40)
        btn_config.clicked.connect(abrir_configuracoes)
        btn_config.setStyleSheet("border-radius: 20px; font-size: 20px;")

        layout_principal.addStretch()
        layout_principal.addWidget(btn_config, alignment=Qt.AlignBottom | Qt.AlignRight)

    def gerar_planilha(self):
        msg = QMessageBox()
        msg.setWindowTitle("Escolha o Tipo de Relatório")
        msg.setText("Deseja gerar qual planilha?")
        btn_fiados = msg.addButton("💸 Valores em Aberto", QMessageBox.AcceptRole)
        btn_pagos = msg.addButton("✅ Valores Pagos", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == btn_fiados:
            caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha", "valores_abertos.csv", "CSV (*.csv)")
            if caminho:
                gerar_planilha_resumo(caminho)
                QMessageBox.information(self, "Sucesso", f"Planilha salva em: {caminho}")

        elif msg.clickedButton() == btn_pagos:
            caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha", "valores_pagos.csv", "CSV (*.csv)")
            if caminho:
                gerar_planilha_pagos(caminho)
                QMessageBox.information(self, "Sucesso", f"Planilha salva em: {caminho}")

class DialogFormaPagamento(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forma de Pagamento")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Escolha a forma de pagamento:"))

        self.combo = QComboBox()
        self.combo.addItems(["PIX/Transferência", "Dinheiro/Cheque"])
        layout.addWidget(self.combo)

        self.botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botoes.accepted.connect(self.accept)
        self.botoes.rejected.connect(self.reject)
        layout.addWidget(self.botoes)

        self.setLayout(layout)

    def forma_escolhida(self):
        return self.combo.currentText()

class TelaClientes(QWidget):
    def __init__(self, voltar, abrir_perfil):
        super().__init__()
        layout = QVBoxLayout()
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome")

        self.telefone = QLineEdit()
        self.telefone.setPlaceholderText("Telefone")
        self.telefone.setInputMask("(00)00000-0000")
        self.telefone.setCursorPosition(1)

        self.obs = QTextEdit()
        self.obs.setPlaceholderText("Observações")
        self.obs.setFixedHeight(50)

        self.btn_salvar = QPushButton("Salvar Cliente")
        self.btn_salvar.clicked.connect(self.salvar_cliente)

        btn_voltar = QPushButton("⬅ Voltar ao Início")
        btn_voltar.clicked.connect(voltar)

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("🔍 Buscar cliente")
        self.busca.textChanged.connect(self.filtrar_clientes)

        self.lista = QTableWidget()
        self.lista.setColumnCount(7)
        self.lista.setHorizontalHeaderLabels([
            "ID", "Nome", "Telefone", "Observação", "Editar", "Excluir", "Ver Perfil"
        ])

        layout.addWidget(self.nome)
        layout.addWidget(self.telefone)
        layout.addWidget(self.obs)
        layout.addWidget(self.btn_salvar)
        layout.addWidget(btn_voltar)
        layout.addWidget(self.busca)
        layout.addWidget(self.lista)
        self.setLayout(layout)

        self.abrir_perfil = abrir_perfil
        self.carregar()

    def salvar_cliente(self):
        nome = self.nome.text().strip()
        telefone = self.telefone.text().strip()
        obs = self.obs.toPlainText().strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "O nome não pode estar vazio.")
            return

        # Verificação de duplicidade (ignora maiúsculas/minúsculas)
        nomes_existentes = [c[1].lower() for c in listar_clientes()]
        if nome.lower() in nomes_existentes and cliente_em_edicao is None:
            QMessageBox.warning(self, "Duplicado", f"Já existe um cliente chamado \"{nome}\".")
            return

        confirmar = QMessageBox.question(
            self,
            "Confirmar Registro",
            f"Deseja salvar o cliente \"{nome}\"?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar == QMessageBox.Yes:
            salvar_ou_atualizar_cliente(nome, telefone, obs)
            self.nome.clear()
            self.telefone.clear()
            self.obs.clear()
            self.carregar()

    def carregar(self):
        self.lista.setRowCount(0)
        self.todos_clientes = listar_clientes()
        for cliente in self.todos_clientes:
            self.adicionar_cliente_na_tabela(cliente)

    def adicionar_cliente_na_tabela(self, cliente):
        row = self.lista.rowCount()
        self.lista.insertRow(row)
        for col, val in enumerate(cliente):
            self.lista.setItem(row, col, QTableWidgetItem(str(val)))

        btn_editar = QPushButton("Editar")
        btn_editar.clicked.connect(lambda _, r=row: self.carregar_para_edicao(r))
        self.lista.setCellWidget(row, 4, btn_editar)

        btn_excluir = QPushButton("Excluir")
        btn_excluir.clicked.connect(lambda _, id_cliente=cliente[0]: self.excluir_cliente(id_cliente))
        self.lista.setCellWidget(row, 5, btn_excluir)

        btn_perfil = QPushButton("👤 Perfil")
        btn_perfil.clicked.connect(lambda _, cid=cliente[0]: self.abrir_perfil(cid))
        self.lista.setCellWidget(row, 6, btn_perfil)

    def carregar_para_edicao(self, row):
        self.nome.setText(self.lista.item(row, 1).text())
        self.telefone.setText(self.lista.item(row, 2).text())
        self.obs.setPlainText(self.lista.item(row, 3).text())
        editar_cliente_id(int(self.lista.item(row, 0).text()))

    def excluir_cliente(self, id_cliente):
        confirmar = QMessageBox.question(
            self,
            "Excluir Cliente",
            "Tem certeza que deseja excluir este cliente?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            excluir_cliente(id_cliente)
            self.carregar()

    def filtrar_clientes(self, texto):
        texto = texto.lower()
        self.lista.setRowCount(0)
        for cliente in self.todos_clientes:
            if texto in cliente[1].lower():
                self.adicionar_cliente_na_tabela(cliente)

class TelaProdutos(QWidget):
    def __init__(self, voltar):
        super().__init__()
        layout = QVBoxLayout()
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome do Produto")
        self.preco = QLineEdit()
        self.preco.setPlaceholderText("Preço")
        validador = QDoubleValidator(0.00, 999999.99, 2)
        validador.setNotation(QDoubleValidator.StandardNotation)
        self.preco.setValidator(validador)
        btn_add = QPushButton("Adicionar Produto")
        btn_add.clicked.connect(self.adicionar)
        btn_voltar = QPushButton("⬅ Voltar ao Início")
        btn_voltar.clicked.connect(voltar)
        self.lista = QTableWidget()
        self.lista.setColumnCount(3)
        self.lista.setHorizontalHeaderLabels(["Nome", "Preço", "Excluir"])
        layout.addWidget(self.nome)
        layout.addWidget(self.preco)
        layout.addWidget(btn_add)
        layout.addWidget(btn_voltar)
        layout.addWidget(self.lista)
        self.setLayout(layout)
        self.carregar()

    def adicionar(self):
        nome = self.nome.text().strip()
        preco_texto = self.preco.text().strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "O nome do produto não pode estar vazio.")
            return

        if not preco_texto:
            QMessageBox.warning(self, "Erro", "O preço do produto não pode estar vazio.")
            return

        try:
            preco = float(preco_texto)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preço inválido. Digite um número válido.")
            return

        inserir_produto(nome, preco)
        self.nome.clear()
        self.preco.clear()
        self.carregar()

    def carregar(self):
        self.lista.setRowCount(0)
        for nome, preco in listar_produtos():
            row = self.lista.rowCount()
            self.lista.insertRow(row)
            self.lista.setItem(row, 0, QTableWidgetItem(nome))
            self.lista.setItem(row, 1, QTableWidgetItem(f"R${preco:.2f}"))
            btn_excluir = QPushButton("Excluir")
            btn_excluir.clicked.connect(lambda _, n=nome: self.excluir_por_nome(n))
            self.lista.setCellWidget(row, 2, btn_excluir)

    def excluir_por_nome(self, nome):
        for pid, n, _ in listar_produtos_detalhes():
            if n == nome:
                excluir_produto(pid)
                break
        self.carregar()

class AccentInsensitiveProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index, Qt.DisplayRole)
        if data is None:
            return False

        filter_text = self.filterRegExp().pattern().lower()
        data_normalized = self.normalize(data)
        return filter_text in data_normalized

    def normalize(self, text):
        return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII").lower()

class TelaRegistro(QWidget):
    def __init__(self, voltar):
        super().__init__()
        layout = QVBoxLayout()

        self.cliente_model = QStandardItemModel()
        self.proxy_model = AccentInsensitiveProxyModel()
        self.proxy_model.setSourceModel(self.cliente_model)

        self.cliente = QComboBox()
        self.cliente.setEditable(True)
        self.cliente.setInsertPolicy(QComboBox.NoInsert)
        self.cliente.setPlaceholderText("Cliente")

        completer = QCompleter(self.proxy_model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.cliente.setCompleter(completer)

        layout.addWidget(self.cliente)

        self.produto = QComboBox()
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 9999)
        self.obs = QTextEdit()
        self.obs.setPlaceholderText("Observações do Pedido")
        layout.addWidget(self.obs)

        btn_add = QPushButton("Adicionar Produto")
        btn_add.clicked.connect(self.add_produto)

        layout.addWidget(self.produto)
        layout.addWidget(self.qtd)
        layout.addWidget(btn_add)

        self.lista = QTableWidget()
        self.lista.setColumnCount(6)
        self.lista.setHorizontalHeaderLabels(["Produto", "Qtd", "Preço Unitário", "Subtotal", "Observação", "Excluir"])
        layout.addWidget(self.lista)

        self.label_total = QLabel("Total: R$0.00")
        layout.addWidget(self.label_total)

        btn_registrar = QPushButton("Registrar Pedido")
        btn_registrar.clicked.connect(self.registrar)

        btn_voltar = QPushButton("⬅ Voltar ao Início")
        btn_voltar.clicked.connect(voltar)

        layout.addWidget(btn_registrar)
        layout.addWidget(btn_voltar)

        self.setLayout(layout)

        self.lista.itemChanged.connect(self.atualizar_quantidade)
        self.atualizar()

    def atualizar(self):
        self.cliente_model.clear()
        self.produto.clear()
        for id, nome in listar_clientes_id():
            item = QStandardItem(nome)
            item.setData(id, Qt.UserRole)
            self.cliente_model.appendRow(item)

        for id, nome, preco in listar_produtos_detalhes():
            self.produto.addItem(f"{nome} - R${preco:.2f}", (id, preco))

        self.lista.setRowCount(0)

    def add_produto(self):
        self.lista.itemChanged.disconnect(self.atualizar_quantidade)

        nome = self.produto.currentText().split(" - ")[0]
        (id, preco) = self.produto.currentData()
        qtd = self.qtd.value()
        subtotal = qtd * preco

        row = self.lista.rowCount()
        self.lista.insertRow(row)

        # Produto
        item_nome = QTableWidgetItem(nome)
        item_nome.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.lista.setItem(row, 0, item_nome)

        # Quantidade editável
        item_qtd = QTableWidgetItem(str(qtd))
        item_qtd.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.lista.setItem(row, 1, item_qtd)

        # Preço unitário editável
        item_preco = QTableWidgetItem(f"{preco:.2f}")
        item_preco.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.lista.setItem(row, 2, item_preco)

        # Subtotal não editável
        item_subtotal = QTableWidgetItem(f"{subtotal:.2f}")
        item_subtotal.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.lista.setItem(row, 3, item_subtotal)

        # Observação editável
        item_obs = QTableWidgetItem("")
        item_obs.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.lista.setItem(row, 4, item_obs)

        # Botão Excluir
        btn_excluir = QPushButton("Excluir")
        btn_excluir.clicked.connect(lambda _, r=row: self.excluir_item(r))
        self.lista.setCellWidget(row, 5, btn_excluir)

        self.atualizar_total_pedido()
        self.lista.itemChanged.connect(self.atualizar_quantidade)


    def excluir_item(self, row):
        self.lista.removeRow(row)
        self.atualizar_total_pedido()

    def atualizar_quantidade(self, item):
        row = item.row()
        col = item.column()

        if col in [1, 2]:
            try:
                qtd = int(self.lista.item(row, 1).text())
                preco = float(self.lista.item(row, 2).text())
                subtotal = qtd * preco
                self.lista.item(row, 3).setText(f"{subtotal:.2f}")
                self.atualizar_total_pedido()
            except (ValueError, AttributeError):
                pass

    def atualizar_total_pedido(self):
        total = 0.0
        for row in range(self.lista.rowCount()):
            total += float(self.lista.item(row, 3).text())
        self.label_total.setText(f"Total: R${total:.2f}")

    def limpar_campos(self):
        self.obs.clear()
        self.lista.setRowCount(0)
        self.qtd.setValue(1)
        if self.produto.count() > 0:
            self.produto.setCurrentIndex(0)
        if self.cliente.count() > 0:
            self.cliente.setCurrentIndex(0)
        self.label_total.setText("Total: R$0.00")

    def registrar(self):
        texto_cliente = self.cliente.currentText()
        cliente_id = None

        for i in range(self.cliente_model.rowCount()):
            item = self.cliente_model.item(i)
            if item.text().lower().strip() == texto_cliente.lower().strip():
                cliente_id = item.data(Qt.UserRole)
                break

        if not cliente_id:
            QMessageBox.warning(self, "Erro", "Cliente inválido.")
            return

        produtos = []
        for row in range(self.lista.rowCount()):
            nome = self.lista.item(row, 0).text()
            qtd = int(self.lista.item(row, 1).text())
            subtotal = float(self.lista.item(row, 3).text())
            obs_item = self.lista.item(row, 4).text()

            for id, n, preco in listar_produtos_detalhes():
                if n == nome:
                    produtos.append((id, qtd, subtotal, obs_item))
                    break

        observacao = self.obs.toPlainText()

        registrar_pedido(cliente_id, datetime.now().strftime('%Y-%m-%d'), produtos, observacao)

        QMessageBox.information(self, "Sucesso", "Pedido registrado com sucesso!")
        self.limpar_campos()

class TelaFiados(QWidget):
    def __init__(self, voltar):
        super().__init__()
        layout = QVBoxLayout()

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar cliente")
        self.busca.textChanged.connect(self.filtrar)
        layout.addWidget(self.busca)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(15)
        self.tabela.setHorizontalHeaderLabels([
            "Data", "Cliente", "Produto", "Qtd", "Preço Unitário", "Subtotal",
            "Total Pedido", "Valor Pago", "Pedido ID", "Status", "Observação", "Receber", "Excluir", "ProdutoID", "ItemID"
        ])
        self.tabela.setColumnHidden(13, True)
        self.tabela.setColumnHidden(14, True)

        layout.addWidget(self.tabela)

        btn_voltar = QPushButton("⬅ Voltar ao Início")
        btn_voltar.clicked.connect(voltar)
        layout.addWidget(btn_voltar)

        btn_salvar = QPushButton("📂 Salvar Alterações")
        btn_salvar.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(btn_salvar)

        self.setLayout(layout)
        self.todos = []
        self.carregar()

    def carregar(self):
        todos_os_itens = listar_pedidos_detalhados()

        totais_por_pedido = {}
        for item in todos_os_itens:
            pedido_id = item[7]
            if pedido_id not in totais_por_pedido:
                totais_por_pedido[pedido_id] = {
                    "total_pedido": item[10],
                    "valor_pago": item[6]
                }

        self.todos = [
            item for item in todos_os_itens
            if totais_por_pedido[item[7]]["valor_pago"] < totais_por_pedido[item[7]]["total_pedido"]
        ]

        self.detalhes = self.todos[:]
        self.mostrar(self.todos)

    def mostrar(self, lista):
        self.tabela.setRowCount(0)
        cores = ["#3a3a3a", "#2b2b2b"]
        cor_atual = 0
        ultimo_id = None

        for linha in lista:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            pedido_id = linha[7]
            if pedido_id != ultimo_id:
                cor_atual = (cor_atual + 1) % len(cores)
                ultimo_id = pedido_id

            cor_fundo = QColor(cores[cor_atual])

            itens = [
                str(linha[3]),
                str(linha[0]),
                str(linha[1]),
                str(linha[2]),
                f"R${linha[4]:.2f}",
                f"R${linha[5]:.2f}",
                f"R${linha[10]:.2f}",
                f"R${linha[6]:.2f}",
                str(linha[7])
            ]

            for col, valor in enumerate(itens):
                item = QTableWidgetItem(valor)
                item.setBackground(cor_fundo)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.tabela.setItem(row, col, item)

            valor_pago = linha[6]
            total_pedido = linha[10]
            status = "Quitado" if valor_pago >= total_pedido else ("Pago Parcial" if valor_pago > 0 else "Aberto")
            item_status = QTableWidgetItem(status)
            item_status.setBackground(cor_fundo)
            item_status.setFlags(item_status.flags() | Qt.ItemIsEditable)
            self.tabela.setItem(row, 9, item_status)

            item_obs = QTableWidgetItem(str(linha[8]) if linha[8] else "")
            item_obs.setBackground(cor_fundo)
            item_obs.setFlags(item_obs.flags() | Qt.ItemIsEditable)
            self.tabela.setItem(row, 10, item_obs)

            btn_receber = QPushButton("💰 Receber")
            btn_receber.clicked.connect(lambda _, pid=pedido_id: self.receber(pid))
            self.tabela.setCellWidget(row, 11, btn_receber)

            btn_excluir = QPushButton("Excluir")
            btn_excluir.clicked.connect(lambda _, pid=pedido_id: self.excluir(pid))
            self.tabela.setCellWidget(row, 12, btn_excluir)

            item_produto_id = QTableWidgetItem(str(linha[9]))
            item_produto_id.setFlags(Qt.ItemIsEnabled)
            self.tabela.setItem(row, 13, item_produto_id)

            item_item_id = QTableWidgetItem(str(linha[11]))
            item_item_id.setFlags(Qt.ItemIsEnabled)
            self.tabela.setItem(row, 14, item_item_id)

    def excluir(self, pedido_id):
        cliente = "?"
        valor = 0.0
        for linha in self.detalhes:
            if linha[7] == pedido_id:
                cliente = linha[1]
                valor = linha[6]
                break

        resp = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja excluir o pedido de {cliente} no valor de R${valor:.2f}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            excluir_pedido(pedido_id)
            self.carregar()

    def receber(self, pedido_id):
        cliente = "Desconhecido"
        total = 0.0
        pago = 0.0

        for linha in self.detalhes:
            if str(linha[7]) == str(pedido_id):
                cliente = linha[0]
                total = linha[10]
                pago = linha[6]
                break

        restante = max(total - pago, 0)

        valor, ok = QInputDialog.getDouble(
            self,
            "Receber Pagamento",
            f"Quanto deseja receber de {cliente}?\n(Total: R${total:.2f} | Restante: R${restante:.2f})",
            decimals=2,
            min=0,
            max=restante
        )

        if ok and valor > 0:
            forma, ok_forma = QInputDialog.getItem(
                self,
                "Forma de Pagamento",
                "Selecione a forma de pagamento:",
                ["PIX/Transferência", "Dinheiro/Cheque"],
                editable=False
            )

            if ok_forma:
                confirmar = QMessageBox.question(
                    self,
                    "Confirmar Pagamento",
                    f"Confirma o recebimento de R${valor:.2f} do cliente {cliente} via {forma}?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if confirmar == QMessageBox.Yes:
                    registrar_pagamento_parcial(pedido_id, valor, forma)
                    self.carregar()

    def filtrar(self):
        texto = self.busca.text().lower()
        filtrado = [l for l in self.todos if texto in l[0].lower()]
        self.mostrar(filtrado)

    def salvar_alteracoes(self):
        for row in range(self.tabela.rowCount()):
            data = self.tabela.item(row, 0).text()
            cliente = self.tabela.item(row, 1).text()
            produto = self.tabela.item(row, 2).text()
            quantidade = int(self.tabela.item(row, 3).text())

            preco_unitario_str = self.tabela.item(row, 4).text().replace("R$", "").replace(",", "").strip()
            preco_unitario = float(preco_unitario_str)
            subtotal = round(preco_unitario * quantidade, 2)  # ✅ Recalcula corretamente

            valor_pago_str = self.tabela.item(row, 7).text().replace("R$", "").replace(",", "").strip()
            valor_pago = float(valor_pago_str)

            pedido_id = int(self.tabela.item(row, 8).text())
            observacao = self.tabela.item(row, 10).text()
            produto_id = int(self.tabela.item(row, 13).text())
            item_id = int(self.tabela.item(row, 14).text())

            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                UPDATE pedidos SET data = ?, valor_pago = ?, observacao = ?
                WHERE id = ?
            """, (data, valor_pago, observacao, pedido_id))

            cur.execute("""
                UPDATE itens_pedido 
                SET quantidade = ?, preco_unitario = ?, subtotal = ?
                WHERE id = ? AND produto_id = ? AND pedido_id = ?
            """, (quantidade, preco_unitario, subtotal, item_id, produto_id, pedido_id))

            conn.commit()
            conn.close()

        QMessageBox.information(self, "Sucesso", "Alterações salvas com sucesso!")
        self.carregar()

class TelaPerfilCliente(QWidget):
    def __init__(self, cliente_id, voltar_callback):
        super().__init__()
        self.id_cliente = cliente_id
        self.voltar_callback = voltar_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label_info = QLabel("")
        layout.addWidget(self.label_info)

        self.filtro_status = QComboBox()
        self.filtro_status.addItems(["Todos", "Abertos/Pagos Parciais"])
        self.filtro_status.currentIndexChanged.connect(lambda: self.carregar(self.id_cliente))
        layout.addWidget(QLabel("Filtrar Pedidos:"))
        layout.addWidget(self.filtro_status)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(15)
        self.tabela.setHorizontalHeaderLabels([
            "Data Emissão", "Data Pagamento", "Produto", "Qtd", "Preço Unitário",
            "Subtotal", "Total Pedido", "Valor Pago", "Valor Restante", "Pedido ID", "Status",
            "Observação", "Receber", "Excluir", "Item ID"
        ])
        self.tabela.setColumnHidden(14, True)  # Oculta Item ID
        layout.addWidget(self.tabela)

        btn_voltar = QPushButton("⬅ Voltar")
        btn_voltar.clicked.connect(self.voltar_callback)
        layout.addWidget(btn_voltar)

        btn_salvar = QPushButton("💾 Salvar Alterações")
        btn_salvar.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(btn_salvar)

        btn_pdf = QPushButton("📁 Gerar PDF da Ficha")
        btn_pdf.clicked.connect(self.gerar_pdf)
        layout.addWidget(btn_pdf)

        self.setLayout(layout)
        self.carregar(self.id_cliente)

    def carregar(self, cliente_id):
        self.id_cliente = cliente_id
        dados = listar_pedidos_por_cliente(cliente_id)
        self.tabela.setRowCount(0)

        nome, total_pago, total_aberto = obter_nome_e_totais_cliente(cliente_id)
        self.label_info.setText(f"<b>{nome}</b> | Total Pago: R${total_pago:.2f} | Total em Aberto: R${total_aberto:.2f}")

        cores = ["#3a3a3a", "#2b2b2b"]
        cor_atual = 0
        pedido_anterior = None
        self.detalhes = dados

        # Ordenar os dados por data (mais antigos primeiro)
        dados.sort(key=lambda x: x[0])

        # Filtragem por status se necessário
        filtro = self.filtro_status.currentText()
        if filtro == "Abertos/Pagos Parciais":
            dados = [
                linha for linha in dados
                if linha[6] < linha[9]  # valor_pago < total_pedido
            ]

        for linha in dados:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            emissao, pagamento, produto, qtd, preco_unitario, subtotal, valor_pago, pedido_id, item_obs, total_pedido, item_id = linha

            status = "Quitado" if valor_pago >= total_pedido else ("Pago Parcial" if valor_pago > 0 else "Aberto")
            valor_restante = max(total_pedido - valor_pago, 0)

            if pedido_id != pedido_anterior:
                cor_atual = (cor_atual + 1) % len(cores)
                pedido_anterior = pedido_id
            cor_fundo = QColor(cores[cor_atual])

            itens = [
                emissao,
                pagamento if pagamento else "—",
                produto,
                str(qtd),
                f"R${preco_unitario:.2f}",
                f"R${subtotal:.2f}",
                f"R${total_pedido:.2f}",
                f"R${valor_pago:.2f}",
                f"R${valor_restante:.2f}",
                str(pedido_id),
                status,
                item_obs
            ]

            for col, valor in enumerate(itens):
                item = QTableWidgetItem(valor)
                item.setBackground(cor_fundo)
                if col in [1, 11]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, col, item)

            if status != "Quitado":
                btn_receber = QPushButton("Receber")
                btn_receber.clicked.connect(lambda _, pid=pedido_id: self.receber_pedido(pid))
                self.tabela.setCellWidget(row, 12, btn_receber)
            else:
                item_placeholder = QTableWidgetItem("")
                item_placeholder.setBackground(cor_fundo)
                self.tabela.setItem(row, 12, item_placeholder)

            btn_excluir = QPushButton("Excluir")
            btn_excluir.clicked.connect(lambda _, pid=pedido_id: self.excluir_pedido(pid))
            self.tabela.setCellWidget(row, 13, btn_excluir)

            item_id_widget = QTableWidgetItem(str(item_id))
            item_id_widget.setFlags(Qt.ItemIsEnabled)
            self.tabela.setItem(row, 14, item_id_widget)

        self.nome_cliente = nome

    def receber_pedido(self, pedido_id):
        cliente = self.nome_cliente
        total = 0.0
        pago = 0.0

        for linha in self.detalhes:
            if str(linha[7]) == str(pedido_id):
                total = linha[9]
                pago = linha[6]
                break

        restante = max(total - pago, 0)

        valor, ok = QInputDialog.getDouble(
            self,
            "Receber Pagamento",
            f"Quanto deseja receber de {cliente}?\n(Total: R${total:.2f} | Restante: R${restante:.2f})",
            decimals=2,
            min=0,
            max=restante
        )

        if ok and valor > 0:
            dialog = DialogFormaPagamento()
            if dialog.exec_() == QDialog.Accepted:
                forma = dialog.forma_escolhida()

                novo_pago = pago + valor
                status = (
                    "Quitado" if novo_pago >= total
                    else "Pago Parcial" if novo_pago > 0
                    else "Aberto"
                )

                confirmacao = QMessageBox.question(
                    self,
                    "Confirmar Pagamento",
                    f"Confirma o recebimento de R${valor:.2f} ({forma}) do cliente {cliente}?\nStatus: {status}",
                    QMessageBox.Yes | QMessageBox.No
                )

                if confirmacao == QMessageBox.Yes:
                    conn = sqlite3.connect("fiados.db")
                    cur = conn.cursor()

                    # garantir que a tabela pagamentos tenha a coluna forma_pagamento
                    cur.execute("PRAGMA table_info(pagamentos)")
                    colunas = [c[1] for c in cur.fetchall()]
                    if "forma_pagamento" not in colunas:
                        cur.execute("ALTER TABLE pagamentos ADD COLUMN forma_pagamento TEXT")

                    cur.execute("""
                        INSERT INTO pagamentos (pedido_id, data, valor, forma_pagamento)
                        VALUES (?, DATE('now'), ?, ?)
                    """, (pedido_id, valor, forma))

                    # Atualizar valor pago
                    cur.execute("SELECT SUM(valor) FROM pagamentos WHERE pedido_id = ?", (pedido_id,))
                    novo_valor_pago = cur.fetchone()[0] or 0

                    cur.execute("SELECT SUM(subtotal) FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))
                    total_do_pedido = cur.fetchone()[0] or 0

                    if novo_valor_pago >= total_do_pedido:
                        cur.execute("UPDATE pedidos SET valor_pago = ?, data_pagamento = DATE('now') WHERE id = ?", (total_do_pedido, pedido_id))
                    else:
                        cur.execute("UPDATE pedidos SET valor_pago = ?, data_pagamento = COALESCE(data_pagamento, DATE('now')) WHERE id = ?", (novo_valor_pago, pedido_id))

                    conn.commit()
                    conn.close()
                    self.carregar(self.id_cliente)

    def excluir_pedido(self, pedido_id):
        if QMessageBox.question(self, "Confirmação", "Deseja realmente excluir este pedido?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            excluir_pedido(pedido_id)
            self.carregar(self.id_cliente)

    def salvar_alteracoes(self):
        for row in range(self.tabela.rowCount()):
            data_emissao = self.tabela.item(row, 0).text()
            data_pagamento = self.tabela.item(row, 1).text().strip()
            produto = self.tabela.item(row, 2).text()
            quantidade = int(self.tabela.item(row, 3).text())
            preco_unitario = float(self.tabela.item(row, 4).text().replace("R$", "").strip())
            subtotal = float(self.tabela.item(row, 5).text().replace("R$", "").strip())
            total_pedido = float(self.tabela.item(row, 6).text().replace("R$", "").strip())
            valor_pago = float(self.tabela.item(row, 7).text().replace("R$", "").strip())
            pedido_id = int(self.tabela.item(row, 8).text())
            observacao = self.tabela.item(row, 10).text()
            item_id = int(self.tabela.item(row, 13).text())

            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                UPDATE pedidos 
                SET data = ?, valor_pago = ?, observacao = ?, data_pagamento = ?
                WHERE id = ?
            """, (
                data_emissao,
                valor_pago,
                observacao,
                data_pagamento if data_pagamento != "—" else None,
                pedido_id
            ))

            cur.execute("""
                UPDATE itens_pedido 
                SET quantidade = ?, preco_unitario = ?, subtotal = ?
                WHERE id = ?
            """, (
                quantidade,
                preco_unitario,
                subtotal,
                item_id
            ))

            conn.commit()
            conn.close()

        QMessageBox.information(self, "Sucesso", "Alterações salvas com sucesso!")
        self.carregar(self.id_cliente)

    def gerar_pdf(self):
        # Carrega configuração da empresa e logo
        nome_empresa = "Minha Empresa"
        logo_path = ""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                nome_empresa = config.get("nome_empresa", nome_empresa)
                logo_path = config.get("logo_path", logo_path)
                detalhamento = config.get("detalhamento", "Detalhamento")

        # Carrega os arquivos HTML e CSS
        with open(caminho_recurso("templates/ficha.html"), "r", encoding="utf-8") as f:
            html_base = f.read()
        with open(caminho_recurso("estilos/ficha.css"), "r", encoding="utf-8") as f:
            css = f.read()

        # Gera a tabela HTML
        colunas_exibidas = [
            "Data Emissão", "Produto", "Qtd", "Preço Unitário",
            "Subtotal", "Total Pedido", "Valor Pago", "Valor Restante", "Status"
        ]
        tabela_html = "<table><thead><tr>" + "".join(f"<th>{col}</th>" for col in colunas_exibidas) + "</tr></thead><tbody>"
        total_aberto = 0.0

        for row in range(self.tabela.rowCount()):
            status = self.tabela.item(row, 10).text()
            if status == "Quitado":
                continue

            data = self.tabela.item(row, 0).text()
            produto = self.tabela.item(row, 2).text()
            qtd = self.tabela.item(row, 3).text()
            preco_unit = self.tabela.item(row, 4).text()
            subtotal = self.tabela.item(row, 5).text()
            total_pedido = self.tabela.item(row, 6).text()
            valor_pago = self.tabela.item(row, 7).text()
            valor_restante = self.tabela.item(row, 8).text()

            try:
                total_aberto += float(valor_restante.replace("R$", "").replace(",", "."))
            except:
                pass

            campos = [data, produto, qtd, preco_unit, subtotal, total_pedido, valor_pago, valor_restante, status]
            tabela_html += "<tr>" + "".join(f"<td>{campo}</td>" for campo in campos) + "</tr>"
        tabela_html += "</tbody></table>"

        # Insere a logo como base64
        logo_html = ""
        if logo_path:
            try:
                logo_real_path = caminho_recurso(logo_path) if not os.path.isabs(logo_path) else logo_path
                with open(logo_real_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode('utf-8')
                    ext = os.path.splitext(logo_real_path)[1].replace('.', '')
                    logo_html = f'<img class="logo-img" src="data:image/{ext};base64,{encoded}">'
            except Exception as e:
                print(f"Erro ao carregar logo: {e}")

        # Preenche o HTML final
        html_final = html_base \
            .replace("{{logo}}", logo_html) \
            .replace("{{empresa}}", nome_empresa) \
            .replace("{{cliente_nome}}", self.nome_cliente) \
            .replace("{{data}}", datetime.now().strftime("%Y-%m-%d")) \
            .replace("{{tabela}}", tabela_html) \
            .replace("{{total_aberto}}", f"{total_aberto:,.2f}".replace(".", ",")) \
            .replace("{{detalhamento}}", detalhamento) \
            .replace("{{estilo}}", css)

        # Salva o PDF
        nome_formatado = self.nome_cliente.replace(" ", "_")
        caminho_pdf, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Ficha em PDF",
            f"{nome_formatado}_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            "PDF Files (*.pdf)"
        )
        if not caminho_pdf:
            return

        try:
            HTML(string=html_final).write_pdf(caminho_pdf)
            QMessageBox.information(self, "PDF Gerado", f"Ficha salva em:\n{caminho_pdf}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF:\n{e}")

def caminho_recurso(relativo):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath("."), relativo)

class CalendarioEstilizado(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MeuCalendario")
        self.aplicar_cores_finais()

    def aplicar_cores_finais(self):
        formato_domingo = QTextCharFormat()
        formato_domingo.setForeground(QColor("red"))
        formato_sabado = QTextCharFormat()
        formato_sabado.setForeground(QColor("red"))

        ano = self.selectedDate().year()
        mes = self.selectedDate().month()
        for dia in range(1, 32):
            try:
                data = QDate(ano, mes, dia)
                if data.dayOfWeek() == 7:
                    self.setDateTextFormat(data, formato_domingo)
                elif data.dayOfWeek() == 6:
                    self.setDateTextFormat(data, formato_sabado)
            except:
                continue

class TelaRecebimentos(QWidget):
    def __init__(self, voltar_callback):
        super().__init__()
        self.voltar_callback = voltar_callback

        layout = QVBoxLayout()

        data_layout = QHBoxLayout()
        label_data = QLabel("Data:")
        self.data_edit = QDateEdit(calendarPopup=True)
        self.data_edit.calendarWidget().setObjectName("MeuCalendario")
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.dateChanged.connect(self.carregar_por_data)

        label_filtro = QLabel("Filtro:")
        self.filtro_combo = QComboBox()
        self.filtro_combo.addItems(["Por Dia", "Por Mês", "Por Ano"])
        self.filtro_combo.currentIndexChanged.connect(self.carregar_por_data)

        data_layout.addWidget(label_data)
        data_layout.addWidget(self.data_edit)
        data_layout.addWidget(label_filtro)
        data_layout.addWidget(self.filtro_combo)
        layout.addLayout(data_layout)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Data Pagamento", "Valor Recebido", "Forma", "ID"])
        layout.addWidget(self.tabela)

        self.total_label = QLabel("Total Recebido: R$0.00")
        self.pix_label = QLabel("Total PIX/Transferência: R$0.00")
        self.dinheiro_label = QLabel("Total Dinheiro/Cheque: R$0.00")
        layout.addWidget(self.total_label)
        layout.addWidget(self.pix_label)
        layout.addWidget(self.dinheiro_label)

        btn_salvar = QPushButton("💾 Salvar Alterações")
        btn_salvar.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(btn_salvar)

        btn_voltar = QPushButton("⬅ Voltar")
        btn_voltar.clicked.connect(self.voltar_callback)
        layout.addWidget(btn_voltar)

        self.setLayout(layout)
        self.carregar_por_data()

    def carregar_por_data(self):
        filtro = self.filtro_combo.currentText()
        data_qdate = self.data_edit.date()
        data_str = data_qdate.toString("yyyy-MM-dd")

        conn_data = datetime.strptime(data_str, "%Y-%m-%d")

        if filtro == "Por Dia":
            dados = listar_pagamentos_por_data(data_str)
        else:
            dados = self.listar_todos_recebimentos()

        if filtro == "Por Mês":
            mes = conn_data.month
            ano = conn_data.year
            dados = [linha for linha in dados if datetime.strptime(linha[2], "%Y-%m-%d").month == mes and datetime.strptime(linha[2], "%Y-%m-%d").year == ano]
        elif filtro == "Por Ano":
            ano = conn_data.year
            dados = [linha for linha in dados if datetime.strptime(linha[2], "%Y-%m-%d").year == ano]

        self.tabela.setRowCount(0)
        total = 0.0
        total_pix = 0.0
        total_dinheiro = 0.0

        for linha in dados:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            pagamento_id, cliente, data_pagamento, valor_pago, forma_pagamento = linha
            total += valor_pago

            if forma_pagamento == "PIX/Transferência":
                total_pix += valor_pago
            elif forma_pagamento == "Dinheiro/Cheque":
                total_dinheiro += valor_pago

            self.tabela.setItem(row, 0, QTableWidgetItem(cliente))

            item_data = QTableWidgetItem(str(data_pagamento))
            item_data.setFlags(item_data.flags() | Qt.ItemIsEditable)
            self.tabela.setItem(row, 1, item_data)

            item_valor = QTableWidgetItem(f"R${valor_pago:.2f}")
            item_valor.setTextAlignment(Qt.AlignCenter)
            item_valor.setFlags(item_valor.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 2, item_valor)

            item_forma = QTableWidgetItem(forma_pagamento or "-")
            item_forma.setFlags(item_forma.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 3, item_forma)

            item_id = QTableWidgetItem(str(pagamento_id))
            item_id.setFlags(Qt.ItemIsEnabled)
            self.tabela.setItem(row, 4, item_id)

        self.tabela.setColumnHidden(4, True)
        self.total_label.setText(f"Total Recebido: R${total:.2f}")
        self.pix_label.setText(f"Total PIX/Transferência: R${total_pix:.2f}")
        self.dinheiro_label.setText(f"Total Dinheiro/Cheque: R${total_dinheiro:.2f}")

    def listar_todos_recebimentos(self):
        todas_datas = []
        hoje = QDate.currentDate()
        for offset in range(365):
            dia = hoje.addDays(-offset)
            data_str = dia.toString("yyyy-MM-dd")
            dados = listar_recebimentos_por_data(data_str)
            todas_datas.extend(dados)
        return todas_datas

    def salvar_alteracoes(self):
        conn = conectar()
        cur = conn.cursor()

        for row in range(self.tabela.rowCount()):
            nova_data = self.tabela.item(row, 1).text()
            pagamento_id = int(self.tabela.item(row, 4).text())

            cur.execute("""
                UPDATE pagamentos
                SET data = ?
                WHERE id = ?
            """, (nova_data, pagamento_id))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Sucesso", "Alterações salvas com sucesso!")
        self.carregar_por_data()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fichas 3 Guris")
        self.setGeometry(100, 100, 600, 500)
        criar_banco()

        self.stack = AnimatedStackedWidget()

        self.recebimentos = TelaRecebimentos(lambda: self.mudar(0))

        self.telas = [
            TelaInicial(self.mudar, self.abrir_configuracoes),
            TelaClientes(lambda: self.mudar(0), self.abrir_perfil),
            TelaProdutos(lambda: self.mudar(0)),
            TelaRegistro(lambda: self.mudar(0)),
            TelaFiados(lambda: self.mudar(0)),
            self.recebimentos,
        ]

        for tela in self.telas:
            self.stack.addWidget(tela)

        self.setCentralWidget(self.stack)

    def mudar(self, index):
        if index == 3:
            self.telas[3].atualizar()
        elif index == 4:
            self.telas[4].carregar()
        self.stack.setCurrentIndexAnimated(index)

    def abrir_perfil(self, cliente_id):
        self.perfil = TelaPerfilCliente(cliente_id, lambda: self.mudar(1))
        self.stack.addWidget(self.perfil)
        self.stack.setCurrentWidget(self.perfil)

    def carregar_clientes(self):
        self.lista.setRowCount(0)
        for cliente in listar_clientes():
            row = self.lista.rowCount()
            self.lista.insertRow(row)

            id_cliente = cliente[0]
            nome = cliente[1]
            telefone = cliente[2]
            observacao = cliente[3]

            self.lista.setItem(row, 0, QTableWidgetItem(str(id_cliente)))
            self.lista.setItem(row, 1, QTableWidgetItem(nome))
            self.lista.setItem(row, 2, QTableWidgetItem(telefone))
            self.lista.setItem(row, 3, QTableWidgetItem(observacao))

            btn_editar = QPushButton("Editar")
            btn_excluir = QPushButton("Excluir")
            btn_perfil = QPushButton("Ver Perfil")

            btn_perfil.clicked.connect(lambda _, cid=id_cliente: self.abrir_perfil(cid))

            self.lista.setCellWidget(row, 4, btn_editar)
            self.lista.setCellWidget(row, 5, btn_excluir)
            self.lista.setCellWidget(row, 6, btn_perfil)
            
    def abrir_configuracoes(self):
        self.config = TelaConfiguracoes(lambda: self.mudar(0)) 
        self.stack.addWidget(self.config)
        self.stack.setCurrentWidget(self.config)

import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap

CONFIG_PATH = "config.json"

class TelaConfiguracoes(QWidget):
    def __init__(self, voltar_callback):
        super().__init__()
        self.voltar_callback = voltar_callback
        self.init_ui()
        self.carregar_config()

    def init_ui(self):
        layout = QVBoxLayout()

        self.logo_label = QLabel("Nenhum logo carregado")
        self.logo_label.setFixedHeight(150)
        self.logo_label.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        self.logo_label.setScaledContents(True)

        self.btn_logo = QPushButton("Selecionar Logo")
        self.btn_logo.clicked.connect(self.selecionar_logo)

        self.nome_empresa_input = QLineEdit()
        self.nome_empresa_input.setPlaceholderText("Nome da Empresa")

        self.detalhamento_input = QLineEdit()
        self.detalhamento_input.setPlaceholderText("Texto de detalhamento")

        self.btn_salvar = QPushButton("Salvar Configurações")
        self.btn_salvar.clicked.connect(self.salvar_config)

        self.btn_voltar = QPushButton("⬅ Voltar")
        self.btn_voltar.clicked.connect(self.voltar_callback)

        layout.addWidget(QLabel("Nome da Empresa:"))
        layout.addWidget(self.nome_empresa_input)

        layout.addWidget(QLabel("Detalhamento:"))
        layout.addWidget(self.detalhamento_input)

        layout.addWidget(QLabel("Logo da Empresa:"))
        layout.addWidget(self.logo_label)
        layout.addWidget(self.btn_logo)

        layout.addWidget(self.btn_salvar)
        layout.addWidget(self.btn_voltar)

        self.setLayout(layout)

    def selecionar_logo(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar Logo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if caminho:
            self.logo_path = caminho
            pixmap = QPixmap(caminho)
            self.logo_label.setPixmap(pixmap)

    def carregar_config(self):
        self.logo_path = ""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.nome_empresa_input.setText(config.get("nome_empresa", ""))
                self.detalhamento_input.setText(config.get("detalhamento", ""))
                self.logo_path = config.get("logo_path", "")

                if os.path.exists(self.logo_path):
                    self.logo_label.setPixmap(QPixmap(self.logo_path))

    def salvar_config(self):
        config = {
            "nome_empresa": self.nome_empresa_input.text(),
            "logo_path": self.logo_path,
            "detalhamento": self.detalhamento_input.text()
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")

def carregar_configuracoes():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
import sys
import os

if getattr(sys, 'frozen', False):
    dll_path = os.path.join(sys._MEIPASS, "gtk3")
    os.add_dll_directory(dll_path)

from PyQt5.QtWidgets import QApplication
from ui import MainWindow

def caminho_recurso(relativo):
    """Garante que o caminho funcione com PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath("."), relativo)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    try:
        with open(caminho_recurso("estilos/estilo.qss"), "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("⚠️ Arquivo estilo.qss não encontrado!")

    janela = MainWindow()
    janela.show()
    sys.exit(app.exec_())

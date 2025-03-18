
import sys
from PyQt6.QtWidgets import QApplication
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    print("PyQt6-WebEngine carregado com sucesso!")
except ImportError as e:
    print(f"Erro ao importar WebEngine: {e}")
    sys.exit(1)
app = QApplication([])
view = QWebEngineView()
print("QWebEngineView criado com sucesso!")
sys.exit(0)

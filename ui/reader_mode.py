from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, 
                           QPushButton, QSlider, QHBoxLayout, QComboBox,
                           QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImage, QPalette, QColor
from PyQt6.QtWebEngineCore import QWebEngineScript
import re

class ReaderModeWidget(QWidget):
    def __init__(self, parent=None, content=None, title=None, url=None):
        super().__init__(parent)
        self.parent = parent
        self.content = content
        self.title = title
        self.url = url
        self.font_size = 16
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Barra de controle
        control_bar = QHBoxLayout()
        
        close_btn = QPushButton("✕ Fechar")
        close_btn.clicked.connect(self.close_reader)
        control_bar.addWidget(close_btn)
        
        control_bar.addStretch()
        
        font_smaller = QPushButton("A-")
        font_smaller.clicked.connect(self.decrease_font)
        control_bar.addWidget(font_smaller)
        
        font_bigger = QPushButton("A+")
        font_bigger.clicked.connect(self.increase_font)
        control_bar.addWidget(font_bigger)
        
        theme_selector = QComboBox()
        theme_selector.addItems(["Claro", "Escuro", "Sépia"])
        theme_selector.currentIndexChanged.connect(self.change_theme)
        control_bar.addWidget(theme_selector)
        
        layout.addLayout(control_bar)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Título
        if self.title:
            title_label = QLabel(self.title)
            title_font = QFont()
            title_font.setPointSize(20)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setWordWrap(True)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            # URL
            if self.url:
                url_label = QLabel(f"<a href='{self.url}'>{self.url}</a>")
                url_label.setOpenExternalLinks(True)
                url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(url_label)
            
            layout.addSpacing(20)
        
        # Área de conteúdo com rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        self.content_label = QLabel(self.content)
        self.content_label.setWordWrap(True)
        self.update_font_size()
        
        content_layout.addWidget(self.content_label)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        self.change_theme(0)  # Tema claro padrão
    
    def update_font_size(self):
        """Atualiza o tamanho da fonte no conteúdo"""
        font = QFont()
        font.setPointSize(self.font_size)
        self.content_label.setFont(font)
    
    def increase_font(self):
        """Aumenta o tamanho da fonte"""
        self.font_size = min(32, self.font_size + 2)
        self.update_font_size()
    
    def decrease_font(self):
        """Diminui o tamanho da fonte"""
        self.font_size = max(10, self.font_size - 2)
        self.update_font_size()
    
    def change_theme(self, index):
        """Muda o tema da visualização"""
        if index == 0:  # Claro
            self.setStyleSheet("""
                background-color: #FFFFFF;
                color: #000000;
            """)
            self.content_label.setStyleSheet("color: #000000;")
        elif index == 1:  # Escuro
            self.setStyleSheet("""
                background-color: #1E1E1E;
                color: #DEDEDE;
            """)
            self.content_label.setStyleSheet("color: #DEDEDE;")
        elif index == 2:  # Sépia
            self.setStyleSheet("""
                background-color: #F4ECD8;
                color: #5F4B32;
            """)
            self.content_label.setStyleSheet("color: #5F4B32;")
    
    def close_reader(self):
        """Fecha o modo de leitura"""
        self.parent.toggle_reader_mode()


class ReaderModeExtractor:
    """Classe para extrair e limpar conteúdo da página para o modo leitura"""
    @staticmethod
    def extract_content(html):
        """Extrai o conteúdo principal da página HTML"""
        # Remove scripts, estilos e comentários
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Tenta encontrar o conteúdo principal
        main_content_patterns = [
            r'<article.*?>(.*?)</article>',
            r'<div[^>]*?class="[^"]*?(?:content|article|post|entry)[^"]*?".*?>(.*?)</div>',
            r'<div[^>]*?id="[^"]*?(?:content|article|post|entry)[^"]*?".*?>(.*?)</div>',
            r'<main.*?>(.*?)</main>'
        ]
        
        for pattern in main_content_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break
        else:
            content = html  # Fallback: usa todo o HTML
        
        # Remove tags específicas
        unwanted_elements = [
            r'<div[^>]*?class="[^"]*?(?:comment|sidebar|footer|nav|menu|ad|banner)[^"]*?".*?>.*?</div>',
            r'<nav.*?>.*?</nav>',
            r'<footer.*?>.*?</footer>',
            r'<aside.*?>.*?</aside>'
        ]
        
        for pattern in unwanted_elements:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Limpa tags HTML mantendo apenas parágrafos, cabeçalhos e imagens
        content = re.sub(r'<(?!h[1-6]|p|img).*?>|</(?!h[1-6]|p).*?>', '', content)
        
        # Mantém apenas o texto entre tags permitidas
        content_clean = ''
        in_tag = False
        for i, char in enumerate(content):
            if char == '<':
                tag_match = re.match(r'<(h[1-6]|p|img)', content[i:i+10])
                if tag_match:
                    in_tag = True
                    content_clean += char
            elif char == '>':
                content_clean += char
                in_tag = False
            elif in_tag:
                content_clean += char
            else:
                # Não estamos em uma tag permitida, então verificamos se esse é texto útil
                # e não apenas espaço em branco
                if re.match(r'\S', char):
                    content_clean += char
        
        return content_clean

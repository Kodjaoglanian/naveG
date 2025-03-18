from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QScrollArea, QFileDialog, QApplication)
from PyQt6.QtCore import Qt, QSize, QRect, QTimer, QCoreApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QScreen
import os
import datetime

class ScreenshotDialog(QDialog):
    """Diálogo para visualizar e salvar uma captura de tela"""
    
    def __init__(self, parent=None, pixmap=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.setWindowTitle("Captura de Tela")
        self.setMinimumSize(800, 600)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Área de visualização da captura
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        image_container = QWidget()
        container_layout = QVBoxLayout(image_container)
        
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.image_label)
        
        scroll_area.setWidget(image_container)
        layout.addWidget(scroll_area)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_screenshot)
        button_layout.addWidget(save_button)
        
        copy_button = QPushButton("Copiar para Área de Transferência")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_screenshot(self):
        """Salva a captura de tela em um arquivo"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Captura de Tela", 
            f"screenshot_{timestamp}.png", 
            "Imagens (*.png *.jpg)"
        )
        
        if filename:
            self.pixmap.save(filename)
            self.accept()
    
    def copy_to_clipboard(self):
        """Copia a captura para a área de transferência"""
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.pixmap)


class ScreenshotTool:
    """Ferramenta para capturar tela do navegador"""
    
    @staticmethod
    def capture_visible(browser):
        """Captura a parte visível da página"""
        pixmap = browser.grab()
        return pixmap
    
    @staticmethod
    def capture_full_page(browser):
        """Captura a página inteira (rolagem automática)"""
        # Salva a posição original de rolagem
        original_scroll = browser.page().scrollPosition()
        
        # Obtém o tamanho do conteúdo
        size = browser.page().contentsSize()
        
        # Cria uma imagem para armazenar a captura completa
        full_pixmap = QPixmap(size.toSize())
        full_pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(full_pixmap)
        
        # Captura a página em partes, rolando para cada parte
        viewport_height = browser.height()
        for y_pos in range(0, int(size.height()), viewport_height):
            # Rola para a posição
            browser.page().runJavaScript(f"window.scrollTo(0, {y_pos});")
            
            # Dá tempo para renderizar
            QTimer.singleShot(300, lambda: None)
            QCoreApplication.processEvents()
            
            # Captura a parte visível
            part = browser.grab()
            
            # Desenha na imagem completa
            painter.drawPixmap(0, y_pos, part)
        
        painter.end()
        
        # Restaura a posição original de rolagem
        browser.page().runJavaScript(f"window.scrollTo({original_scroll.x()}, {original_scroll.y()});")
        
        return full_pixmap

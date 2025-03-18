from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, 
                           QPushButton, QCheckBox, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineCore import QWebEnginePage

class SearchPanel(QWidget):
    def __init__(self, parent, browser):
        super().__init__(parent)
        self.parent = parent
        self.browser = browser
        self.initUI()
        self.setVisible(False)
    
    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar na página...")
        self.search_input.returnPressed.connect(self.search_forward)
        layout.addWidget(self.search_input)
        
        self.case_sensitive = QCheckBox("Diferenciar maiúsculas/minúsculas")
        layout.addWidget(self.case_sensitive)
        
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.search_backward)
        layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Próximo")
        self.next_button.clicked.connect(self.search_forward)
        layout.addWidget(self.next_button)
        
        self.matches_label = QLabel("")
        layout.addWidget(self.matches_label)
        
        self.close_button = QPushButton("X")
        self.close_button.setMaximumWidth(30)
        self.close_button.clicked.connect(self.hide)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)
    
    def search_forward(self):
        text = self.search_input.text()
        if text:
            flags = self.get_search_flags()
            self.browser.findText(text, flags, self.on_search_result)
    
    def search_backward(self):
        text = self.search_input.text()
        if text:
            flags = self.get_search_flags() | QWebEnginePage.FindFlag.FindBackward
            self.browser.findText(text, flags, self.on_search_result)
    
    def get_search_flags(self):
        flags = QWebEnginePage.FindFlag.FindCaseSensitively if self.case_sensitive.isChecked() else QWebEnginePage.FindFlag.NoFlagsForFind
        return flags
    
    def on_search_result(self, found):
        if found:
            self.matches_label.setText("Encontrado")
            self.matches_label.setStyleSheet("color: green")
        else:
            self.matches_label.setText("Não encontrado")
            self.matches_label.setStyleSheet("color: red")
    
    def showPanel(self):
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def hidePanel(self):
        self.setVisible(False)
        # Limpar destaques quando fechar
        self.browser.findText("")

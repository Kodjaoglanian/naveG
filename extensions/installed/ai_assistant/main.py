from extensions.extension_base import ExtensionBase
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QComboBox)
from PyQt6.QtCore import Qt
import re
from collections import Counter
from bs4 import BeautifulSoup

class AIAssistantDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("AI Page Assistant")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # Modo de análise
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "📊 Análise de Texto",
            "🔍 Extração de Dados",
            "📑 Resumo",
            "🎯 Palavras-chave",
            "🔗 Links Importantes"
        ])
        layout.addWidget(self.mode_combo)
        
        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        # Botões
        analyze_btn = QPushButton("Analisar Página")
        analyze_btn.clicked.connect(self.analyze_page)
        layout.addWidget(analyze_btn)
        
        self.setLayout(layout)
    
    def analyze_page(self):
        mode = self.mode_combo.currentText()
        self.browser.current_browser().page().toHtml(
            lambda html: self.process_content(html, mode))
    
    def process_content(self, html, mode):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        if "Análise de Texto" in mode:
            self.analyze_text(text)
        elif "Extração de Dados" in mode:
            self.extract_data(soup)
        elif "Resumo" in mode:
            self.generate_summary(text)
        elif "Palavras-chave" in mode:
            self.extract_keywords(text)
        elif "Links Importantes" in mode:
            self.analyze_links(soup)
    
    def analyze_text(self, text):
        words = len(text.split())
        sentences = len(re.split(r'[.!?]+', text))
        paragraphs = len(re.split(r'\n\s*\n', text))
        
        result = (
            "📊 Análise de Texto:\n\n"
            f"• Palavras: {words}\n"
            f"• Sentenças: {sentences}\n"
            f"• Parágrafos: {paragraphs}\n"
            f"• Complexidade de leitura: {self.calculate_readability(text)}\n"
        )
        self.result_text.setText(result)
    
    def extract_data(self, soup):
        result = "🔍 Dados Encontrados:\n\n"
        
        # Extrair possíveis dados estruturados
        tables = soup.find_all('table')
        result += f"• Tabelas encontradas: {len(tables)}\n"
        
        # Procurar por dados de contato
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', str(soup))
        phones = re.findall(r'\b\d{2}[\s-]?\d{4,5}[-\s]?\d{4}\b', str(soup))
        
        if emails:
            result += "\n📧 E-mails encontrados:\n"
            result += "\n".join(f"  - {email}" for email in set(emails))
        
        if phones:
            result += "\n📱 Telefones encontrados:\n"
            result += "\n".join(f"  - {phone}" for phone in set(phones))
            
        self.result_text.setText(result)
    
    def generate_summary(self, text):
        # Implementação simples de resumo
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) > 5:
            summary = sentences[:3] + ["..."] + sentences[-2:]
        else:
            summary = sentences
            
        result = "📑 Resumo do Conteúdo:\n\n"
        result += "\n".join(f"• {s}" for s in summary)
        self.result_text.setText(result)
    
    def extract_keywords(self, text):
        # Remover palavras comuns
        common_words = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para'}
        words = re.findall(r'\w+', text.lower())
        words = [w for w in words if w not in common_words and len(w) > 3]
        
        # Contar frequência
        counter = Counter(words)
        keywords = counter.most_common(10)
        
        result = "🎯 Palavras-chave:\n\n"
        for word, count in keywords:
            result += f"• {word}: {count} ocorrências\n"
        self.result_text.setText(result)
    
    def analyze_links(self, soup):
        links = soup.find_all('a')
        result = "🔗 Links Importantes:\n\n"
        
        # Categorizar links
        internal = []
        external = []
        resources = []
        
        current_domain = self.browser.current_browser().url().host()
        
        for link in links:
            href = link.get('href', '')
            text = link.text.strip()
            if not href or not text:
                continue
                
            if href.startswith('#'):
                continue
            elif href.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                resources.append((text, href))
            elif current_domain in href:
                internal.append((text, href))
            else:
                external.append((text, href))
        
        if internal:
            result += "\n📍 Links Internos:\n"
            for text, href in internal[:5]:
                result += f"• {text}\n  {href}\n"
        
        if external:
            result += "\n🌐 Links Externos:\n"
            for text, href in external[:5]:
                result += f"• {text}\n  {href}\n"
        
        if resources:
            result += "\n📁 Recursos:\n"
            for text, href in resources:
                result += f"• {text}\n  {href}\n"
        
        self.result_text.setText(result)
    
    def calculate_readability(self, text):
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        if not words or not sentences:
            return "N/A"
        
        avg_words_per_sentence = len(words) / len(sentences)
        if avg_words_per_sentence > 25:
            return "Complexo"
        elif avg_words_per_sentence > 15:
            return "Moderado"
        else:
            return "Fácil"

class Extension(ExtensionBase):
    def _init(self):
        self.create_action("🤖 AI Assistant", self.show_assistant, "Ctrl+Shift+A")
        self.dialog = None
    
    def show_assistant(self):
        if not self.dialog:
            self.dialog = AIAssistantDialog(self.browser)
        self.dialog.show()
        self.dialog.raise_()

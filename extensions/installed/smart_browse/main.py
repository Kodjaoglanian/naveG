from extensions.extension_base import ExtensionBase
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QWidget, QScrollArea, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QFont
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

class SmartBrowsePanel(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("SmartBrowse")
        self.setGeometry(100, 100, 400, 600)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Barra de ferramentas rápidas
        tools = QHBoxLayout()
        
        self.read_btn = QPushButton("📖 Modo Leitura")
        self.read_btn.clicked.connect(self.toggle_read_mode)
        tools.addWidget(self.read_btn)
        
        self.focus_btn = QPushButton("🎯 Modo Foco")
        self.focus_btn.clicked.connect(self.toggle_focus_mode)
        tools.addWidget(self.focus_btn)
        
        self.trans_btn = QPushButton("🌎 Traduzir")
        self.trans_btn.clicked.connect(self.translate_page)
        tools.addWidget(self.trans_btn)
        
        layout.addLayout(tools)
        
        # Área de recursos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)
        
        # 1. Smart Summary (Resumo Inteligente)
        summary_group = self.create_group("📝 Resumo Inteligente")
        self.summary_text = QLabel("Analisando página...")
        self.summary_text.setWordWrap(True)
        summary_group.layout().addWidget(self.summary_text)
        scroll_layout.addWidget(summary_group)
        
        # 2. Quick Actions (Ações Rápidas)
        actions_group = self.create_group("⚡ Ações Rápidas")
        actions_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Salvar")
        save_btn.clicked.connect(self.save_page)
        actions_layout.addWidget(save_btn)
        
        share_btn = QPushButton("📤 Compartilhar")
        share_btn.clicked.connect(self.share_page)
        actions_layout.addWidget(share_btn)
        
        print_btn = QPushButton("🖨️ Imprimir")
        print_btn.clicked.connect(self.print_page)
        actions_layout.addWidget(print_btn)
        
        actions_group.layout().addLayout(actions_layout)
        scroll_layout.addWidget(actions_group)
        
        # 3. Page Tools (Ferramentas de Página)
        tools_group = self.create_group("🔧 Ferramentas")
        
        # Zoom rápido
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_label)
        
        zoom_out = QPushButton("🔍-")
        zoom_out.clicked.connect(lambda: self.zoom_page(-10))
        zoom_layout.addWidget(zoom_out)
        
        self.zoom_level = QLabel("100%")
        zoom_layout.addWidget(self.zoom_level)
        
        zoom_in = QPushButton("🔍+")
        zoom_in.clicked.connect(lambda: self.zoom_page(10))
        zoom_layout.addWidget(zoom_in)
        
        tools_group.layout().addLayout(zoom_layout)
        
        # Ajuste de fonte
        font_layout = QHBoxLayout()
        font_label = QLabel("Fonte:")
        font_layout.addWidget(font_label)
        
        decrease_font = QPushButton("A-")
        decrease_font.clicked.connect(lambda: self.adjust_font(-1))
        font_layout.addWidget(decrease_font)
        
        self.font_size = QLabel("16px")
        font_layout.addWidget(self.font_size)
        
        increase_font = QPushButton("A+")
        increase_font.clicked.connect(lambda: self.adjust_font(1))
        font_layout.addWidget(increase_font)
        
        tools_group.layout().addLayout(font_layout)
        scroll_layout.addWidget(tools_group)
        
        # 4. Smart Features (Recursos Inteligentes)
        features_group = self.create_group("🎯 Recursos Inteligentes")
        
        # Modo noturno automático
        auto_dark = QPushButton("🌙 Modo Noturno Automático")
        auto_dark.setCheckable(True)
        auto_dark.toggled.connect(self.toggle_auto_dark)
        features_group.layout().addWidget(auto_dark)
        
        # Bloqueador de distrações
        distraction_block = QPushButton("🚫 Bloqueador de Distrações")
        distraction_block.setCheckable(True)
        distraction_block.toggled.connect(self.toggle_distraction_block)
        features_group.layout().addWidget(distraction_block)
        
        scroll_layout.addWidget(features_group)
        
        # 5. Page Info (Informações da Página)
        info_group = self.create_group("ℹ️ Informações")
        self.info_text = QLabel("Carregando informações...")
        self.info_text.setWordWrap(True)
        info_group.layout().addWidget(self.info_text)
        scroll_layout.addWidget(info_group)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        
        # Iniciar análise da página
        self.analyze_current_page()
        
        # Timer para atualização automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.analyze_current_page)
        self.update_timer.start(5000)  # Atualiza a cada 5 segundos
    
    def create_group(self, title):
        """Cria um grupo de widgets com título"""
        widget = QWidget()
        widget.setLayout(QVBoxLayout())
        
        label = QLabel(title)
        font = QFont()
        font.setBold(True)
        label.setFont(font)
        
        widget.layout().addWidget(label)
        return widget
    
    def analyze_current_page(self):
        """Analisa a página atual e atualiza as informações"""
        current = self.browser.current_browser()
        if current:
            current.page().toHtml(self.process_page_content)
    
    def process_page_content(self, html):
        """Processa o conteúdo da página"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Encontrar conteúdo principal com fallbacks
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', {'id': 'content'}) or 
                soup.find('div', {'class': 'content'}) or 
                soup.find('body')
            )
            
            if main_content:
                # Procurar parágrafos no conteúdo principal
                paragraphs = main_content.find_all('p')
                if paragraphs:
                    text = ' '.join(p.get_text().strip() for p in paragraphs[:3])
                    self.summary_text.setText(text[:300] + "..." if len(text) > 300 else text)
                else:
                    # Se não encontrar parágrafos, usar todo o texto
                    text = main_content.get_text().strip()
                    self.summary_text.setText(text[:300] + "..." if len(text) > 300 else text)
            else:
                self.summary_text.setText("Não foi possível gerar um resumo desta página.")
            
            # Atualizar informações
            title = soup.title.string if soup.title else "Sem título"
            word_count = len(soup.get_text().split())
            
            info = f"""
            📑 Título: {title}
            📊 Palavras: {word_count:,}
            🔗 Links: {len(soup.find_all('a'))}
            🖼️ Imagens: {len(soup.find_all('img'))}
            """
            self.info_text.setText(info)
            
        except Exception as e:
            self.summary_text.setText("Erro ao analisar página.")
            self.info_text.setText(f"Erro: {str(e)}")
    
    def toggle_read_mode(self):
        """Ativa/desativa modo leitura"""
        current = self.browser.current_browser()
        if current:
            js = """
            if (!document.getElementById('read-mode')) {
                var style = document.createElement('style');
                style.id = 'read-mode';
                style.innerHTML = `
                    body { max-width: 800px; margin: 0 auto; padding: 20px; }
                    p { font-size: 18px; line-height: 1.8; }
                    img { max-width: 100%; height: auto; }
                    .ad, .advertisement, .social-share { display: none !important; }
                `;
                document.head.appendChild(style);
            } else {
                document.getElementById('read-mode').remove();
            }
            """
            current.page().runJavaScript(js)
    
    def toggle_focus_mode(self):
        """Ativa/desativa modo foco"""
        current = self.browser.current_browser()
        if current:
            js = """
            if (!document.getElementById('focus-mode')) {
                var style = document.createElement('style');
                style.id = 'focus-mode';
                style.innerHTML = `
                    body > * { opacity: 0.3; transition: opacity 0.3s; }
                    :hover { opacity: 1 !important; }
                `;
                document.head.appendChild(style);
            } else {
                document.getElementById('focus-mode').remove();
            }
            """
            current.page().runJavaScript(js)
    
    def translate_page(self):
        """Traduz a página atual"""
        current = self.browser.current_browser()
        if current:
            url = current.url().toString()
            translated_url = f"https://translate.google.com/translate?sl=auto&tl=pt&u={url}"
            current.setUrl(QUrl(translated_url))
    
    def save_page(self):
        """Salva página para leitura offline"""
        current = self.browser.current_browser()
        if current:
            current.page().toHtml(lambda html: self.save_html(html))
    
    def save_html(self, html):
        """Salva o HTML em arquivo"""
        from pathlib import Path
        import datetime
        
        # Criar pasta de páginas salvas
        save_dir = Path.home() / "NavegadorPages"
        save_dir.mkdir(exist_ok=True)
        
        # Salvar arquivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_dir / f"page_{timestamp}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.browser.status_bar.showMessage(f"Página salva em: {file_path}", 3000)
    
    def share_page(self):
        """Compartilha a página atual"""
        current = self.browser.current_browser()
        if current:
            url = quote(current.url().toString())  # URL encode
            title = quote(current.page().title())  # URL encode
            
            # Links de compartilhamento atualizados
            share_urls = {
                "WhatsApp": f"https://api.whatsapp.com/send?text={title}%20-%20{url}",
                "Twitter": f"https://twitter.com/intent/tweet?url={url}&text={title}",
                "Facebook": f"https://www.facebook.com/sharer.php?u={url}",
                "LinkedIn": f"https://www.linkedin.com/sharing/share-offsite/?url={url}",
                "Email": f"mailto:?subject={title}&body=Confira esta página: {url}"
            }
            
            # Menu de compartilhamento melhorado
            share_menu = QDialog(self)
            share_menu.setWindowTitle("Compartilhar")
            share_menu.setMinimumWidth(300)
            share_layout = QVBoxLayout()
            
            for platform, share_url in share_urls.items():
                btn = QPushButton(platform)
                # Fix para o erro do webbrowser
                btn.clicked.connect(lambda checked, url=share_url: self.open_share_url(url))
                share_layout.addWidget(btn)
            
            share_menu.setLayout(share_layout)
            share_menu.exec()
    
    def open_share_url(self, url):
        """Abre URL de compartilhamento de forma segura"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.browser.status_bar.showMessage(f"Erro ao compartilhar: {str(e)}", 3000)
    
    def print_page(self):
        """Imprime a página atual"""
        current = self.browser.current_browser()
        if current:
            current.page().print()
    
    def zoom_page(self, delta):
        """Ajusta o zoom da página"""
        current = self.browser.current_browser()
        if current:
            zoom = current.zoomFactor()
            new_zoom = max(0.25, min(5.0, zoom + delta/100))
            current.setZoomFactor(new_zoom)
            self.zoom_level.setText(f"{int(new_zoom*100)}%")
    
    def adjust_font(self, delta):
        """Ajusta o tamanho da fonte"""
        current = self.browser.current_browser()
        if current:
            current_size = int(self.font_size.text().replace('px', ''))
            new_size = max(8, min(32, current_size + delta))
            self.font_size.setText(f"{new_size}px")
            
            js = f"""
            document.body.style.fontSize = '{new_size}px';
            """
            current.page().runJavaScript(js)
    
    def toggle_auto_dark(self, enabled):
        """Ativa/desativa modo noturno automático"""
        if enabled:
            # Verifica hora do dia
            import datetime
            hour = datetime.datetime.now().hour
            if hour >= 18 or hour < 6:  # Noite
                self.apply_dark_mode()
            
            # Agenda próxima verificação
            QTimer.singleShot(60000, lambda: self.toggle_auto_dark(True))
    
    def apply_dark_mode(self):
        """Aplica modo noturno"""
        current = self.browser.current_browser()
        if current:
            js = """
            if (!document.getElementById('dark-mode')) {
                var style = document.createElement('style');
                style.id = 'dark-mode';
                style.innerHTML = `
                    html { filter: invert(90%) hue-rotate(180deg); }
                    img, video { filter: invert(100%) hue-rotate(180deg); }
                `;
                document.head.appendChild(style);
            }
            """
            current.page().runJavaScript(js)
    
    def toggle_distraction_block(self, enabled):
        """Ativa/desativa bloqueador de distrações"""
        current = self.browser.current_browser()
        if current:
            js = """
            if (!document.getElementById('distraction-blocker')) {
                var style = document.createElement('style');
                style.id = 'distraction-blocker';
                style.innerHTML = `
                    .ad, .advertisement, .social-share,
                    .recommended, .trending, .popular,
                    iframe:not([src*="youtube"]),
                    [class*="newsletter"],
                    [class*="popup"],
                    [id*="popup"] { display: none !important; }
                `;
                document.head.appendChild(style);
            } else {
                document.getElementById('distraction-blocker').remove();
            }
            """
            current.page().runJavaScript(js)

class Extension(ExtensionBase):
    def _init(self):
        self.create_action("🎯 SmartBrowse", self.show_panel, "Ctrl+Shift+B")
        self.panel = None
    
    def show_panel(self):
        if not self.panel:
            self.panel = SmartBrowsePanel(self.browser)
        self.panel.show()
        self.panel.raise_()

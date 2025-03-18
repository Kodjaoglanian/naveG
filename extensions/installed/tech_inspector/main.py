from extensions.extension_base import ExtensionBase
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QTextEdit,
                           QPushButton, QTreeWidget, QTreeWidgetItem, QWidget)
from PyQt6.QtGui import QAction  # Add this import
from PyQt6.QtCore import Qt
from urllib.parse import urlparse
import socket
import ssl
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading
from functools import partial

class TechInspectorDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Tech Inspector")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Criar abas
        tabs = QTabWidget()
        
        # Aba de informações técnicas
        tech_tab = QWidget()
        tech_layout = QVBoxLayout()
        self.tech_tree = QTreeWidget()
        self.tech_tree.setHeaderLabels(["Propriedade", "Valor"])
        tech_layout.addWidget(self.tech_tree)
        tech_tab.setLayout(tech_layout)
        tabs.addTab(tech_tab, "🔍 Info Técnica")
        
        # Aba de segurança
        security_tab = QWidget()
        security_layout = QVBoxLayout()
        self.security_text = QTextEdit()
        self.security_text.setReadOnly(True)
        security_layout.addWidget(self.security_text)
        security_tab.setLayout(security_layout)
        tabs.addTab(security_tab, "🔒 Segurança")
        
        # Aba de rede
        network_tab = QWidget()
        network_layout = QVBoxLayout()
        self.network_text = QTextEdit()
        self.network_text.setReadOnly(True)
        network_layout.addWidget(self.network_text)
        network_tab.setLayout(network_layout)
        tabs.addTab(network_tab, "🌐 Rede")
        
        layout.addWidget(tabs)
        
        # Botão de atualizar
        refresh_btn = QPushButton("🔄 Atualizar Análise")
        refresh_btn.clicked.connect(self.analyze_page)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        self.analyze_page()
    
    def get_ssl_info(self, domain, scheme):
        """Obtém informações SSL com timeout e tratamento de erros"""
        try:
            if scheme != 'https':
                return "⚠️ Site não usa HTTPS - Conexão não segura\n"

            # Configurar timeout
            socket.setdefaulttimeout(3)  # 3 segundos de timeout
            
            # Tentar conexão SSL com tratamento de erros
            try:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.connect((domain, 443))
                    cert = s.getpeercert()
                
                return (
                    "🔒 Conexão HTTPS Segura\n\n"
                    f"Certificado SSL:\n"
                    f"- Emitido para: {cert['subject'][0][0][1]}\n"
                    f"- Emitido por: {cert['issuer'][0][0][1]}\n"
                    f"- Válido até: {cert['notAfter']}\n"
                    f"- Versão: {cert['version']}\n"
                )
            except ssl.SSLError:
                return "⚠️ Erro na verificação SSL - Certificado inválido ou não confiável\n"
            except socket.timeout:
                return "⚠️ Tempo excedido ao verificar certificado SSL\n"
            except Exception as e:
                return f"⚠️ Erro ao verificar SSL: {str(e)}\n"
        finally:
            socket.setdefaulttimeout(None)  # Restaurar timeout padrão
    
    def analyze_page(self):
        """Analisa a página atual e atualiza todas as abas"""
        current_page = self.browser.current_browser().page()
        url = current_page.url().toString()
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Análise técnica básica
        self.tech_tree.clear()
        root = QTreeWidgetItem(self.tech_tree, ["Informações do Site"])
        
        # URL info
        url_item = QTreeWidgetItem(root, ["URL"])
        QTreeWidgetItem(url_item, ["Protocolo", parsed_url.scheme])
        QTreeWidgetItem(url_item, ["Domínio", domain])
        QTreeWidgetItem(url_item, ["Caminho", parsed_url.path])
        QTreeWidgetItem(url_item, ["Query", parsed_url.query or "Nenhuma"])
        
        # Informações do navegador
        browser_item = QTreeWidgetItem(root, ["Navegador"])
        profile = current_page.profile()
        QTreeWidgetItem(browser_item, ["User Agent", profile.httpUserAgent()])
        QTreeWidgetItem(browser_item, ["Cookies Permitidos", str(profile.persistentCookiesPolicy() != 0)])
        QTreeWidgetItem(browser_item, ["JavaScript Habilitado", str(current_page.settings().testAttribute(current_page.settings().WebAttribute.JavascriptEnabled))])
        
        try:
            # Informações de rede em thread separada
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(socket.gethostbyname, domain)
                try:
                    ip = future.result(timeout=2)  # 2 segundos timeout
                    network_info = f"IP do servidor: {ip}\n"
                    
                    # Hostname lookup
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                        network_info += f"Hostname: {hostname}\n"
                    except (socket.herror, socket.timeout):
                        network_info += "Hostname: Não disponível\n"
                except TimeoutError:
                    network_info = "Tempo excedido ao resolver DNS\n"
                except Exception as e:
                    network_info = f"Erro ao obter informações de rede: {str(e)}\n"
            
            self.network_text.setText(network_info)
            
            # Informações de segurança em thread separada
            security_info = self.get_ssl_info(domain, parsed_url.scheme)
            
            # Adicionar informações de cookies
            cookies_policy = current_page.profile().persistentCookiesPolicy()
            security_info += "\nPolítica de Cookies:\n"
            security_info += "- Cookies desabilitados\n" if cookies_policy == 0 else "- Cookies permitidos\n"
            
            self.security_text.setText(security_info)
            
        except Exception as e:
            self.tech_tree.addTopLevelItem(QTreeWidgetItem(["Erro", str(e)]))
        
        self.tech_tree.expandAll()

class Extension(ExtensionBase):
    def _init(self):  # Mudado de init para _init
        self.create_action("🔬 Tech Inspector", self.show_inspector, "Ctrl+Shift+I")
        self.dialog = None
    
    def show_inspector(self):
        if not self.dialog:
            self.dialog = TechInspectorDialog(self.browser)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.analyze_page()

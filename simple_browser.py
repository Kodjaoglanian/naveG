import sys
import os
import json
from PyQt6.QtCore import QUrl, QSize, Qt, QPoint, QPropertyAnimation, QTimer, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, 
                           QLineEdit, QVBoxLayout, QWidget, 
                           QPushButton, QStatusBar, QTabWidget,
                           QMenu, QDialog, QLabel, QFormLayout,
                           QComboBox, QMessageBox, QStackedWidget)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut  # Movido QShortcut para cá
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineUrlRequestInterceptor
from config.settings import settings  # Import the settings instance
from ui.settings_dialog import SettingsDialog  # Changed to absolute import
from ui.themes import apply_theme
from ui.history_manager import HistoryManager, HistoryDialog
from ui.search_panel import SearchPanel
from ui.reader_mode import ReaderModeWidget, ReaderModeExtractor
from ui.gestures import GestureAwareWebView, GestureHandler
from ui.screenshot import ScreenshotDialog, ScreenshotTool
from download_manager import DownloadManager  # Add this import
from extensions.extension_manager import ExtensionManager
import datetime

# Caminho para o arquivo de favoritos
BOOKMARKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookmarks.json")
# Caminho para o arquivo de histórico
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

class WebEnginePage(QWebEnginePage):
    """Página web personalizada para suprimir os avisos de console"""
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Ignora mensagens de console JavaScript para manter o console limpo
        pass

class PrivacyInterceptor(QWebEngineUrlRequestInterceptor):
    """Interceptor para aplicar configurações avançadas de privacidade."""
    def __init__(self, do_not_track=False, block_ads=False):
        super().__init__()
        self.do_not_track = do_not_track
        self.block_ads = block_ads
        # Lista simples de domínios de anúncios (pode ser expandida)
        self.ad_domains = ["doubleclick.net", "googlesyndication.com", "adservice.google.com"]
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.block_ads:
            for domain in self.ad_domains:
                if domain in url:
                    info.block(True)
                    return
        # Note: Qt atualmente não permite modificar cabeçalhos em requests
        # para implementar "Do Not Track" diretamente.

class BrowserTab(QWidget):
    """Widget de uma aba do navegador"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = QWebEngineView()
        
        # Define uma página personalizada para suprimir avisos
        page = WebEnginePage(QWebEngineProfile.defaultProfile(), self.browser)
        self.browser.setPage(page)
        
        self.browser.setUrl(QUrl("https://www.google.com"))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Adicionar painel de pesquisa
        self.search_panel = SearchPanel(self, self.browser)
        layout.addWidget(self.search_panel)
        
        # Adicionar modo leitor (inicialmente oculto)
        self.reader_mode = None
        self.reader_visible = False
        
        # Container para web view com gestos
        self.web_container = QStackedWidget()
        
        # Adicionar suporte a gestos
        self.gesture_view = GestureAwareWebView(self)
        
        # Adicione o browser ao layout do gesture_view
        gesture_layout = QVBoxLayout(self.gesture_view)
        gesture_layout.setContentsMargins(0, 0, 0, 0)
        gesture_layout.addWidget(self.browser)
        
        # Inicializar o GestureHandler com o BrowserTab
        self.gesture_handler = GestureHandler(self)
        
        # Adiciona o container de página
        self.web_container.addWidget(self.gesture_view)
        layout.addWidget(self.web_container)
        
        self.setLayout(layout)
    
    def show_search_panel(self):
        """Mostra o painel de busca na página"""
        self.search_panel.showPanel()
    
    def toggle_reader_mode(self):
        """Alterna entre o modo leitor e o modo normal"""
        if not self.reader_visible:
            # Captura o HTML atual para extrair o conteúdo
            self.browser.page().toHtml(self.show_reader_mode)
        else:
            # Voltar para o modo normal
            if self.reader_mode:
                self.web_container.removeWidget(self.reader_mode)
                self.reader_mode.deleteLater()
                self.reader_mode = None
            self.reader_visible = False
    
    def show_reader_mode(self, html):
        """Processa o HTML e mostra o modo leitor"""
        if html:
            # Extrai o conteúdo principal e limpa
            content = ReaderModeExtractor.extract_content(html)
            title = self.browser.page().title()
            url = self.browser.url().toString()
            
            # Cria e adiciona o widget de modo leitor
            self.reader_mode = ReaderModeWidget(self, content, title, url)
            self.web_container.addWidget(self.reader_mode)
            self.web_container.setCurrentWidget(self.reader_mode)
            self.reader_visible = True

class BookmarkDialog(QDialog):
    """Diálogo para adicionar ou editar favoritos"""
    def __init__(self, parent=None, title="", url=""):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Favorito")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.title_input = QLineEdit(title)
        self.url_input = QLineEdit(url)
        
        layout.addRow("Título:", self.title_input)
        layout.addRow("URL:", self.url_input)
        
        buttons_layout = QVBoxLayout()
        
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addRow("", buttons_layout)
        self.setLayout(layout)
    
    def get_data(self):
        """Retorna os dados do favorito"""
        return {
            "title": self.title_input.text(),
            "url": self.url_input.text()
        }

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meu Navegador")
        self.setGeometry(100, 100, 1280, 800)
        
        # Favoritos
        self.bookmarks = self.load_bookmarks()
        
        # Inicializar gerenciador de histórico
        self.history_manager = HistoryManager(HISTORY_FILE)
        
        # Configurar perfil do WebEngine com configurações de privacidade
        profile = QWebEngineProfile.defaultProfile()
        self.privacy_interceptor = PrivacyInterceptor(
            do_not_track=settings.get("privacy", "do_not_track"),
            block_ads=settings.get("privacy", "block_ads")
        )
        # Updated call: use setUrlRequestInterceptor
        profile.setUrlRequestInterceptor(self.privacy_interceptor)
        
        # Criar o widget de abas
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        
        # Configurar o layout principal
        self.setCentralWidget(self.tabs)
        
        # Criar a barra de ferramentas e os botões
        toolbar = QToolBar("Navegação")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)  # Fixa a barra de ferramentas
        self.addToolBar(toolbar)
        
        # Botão de voltar
        back_btn = QAction("←", self)
        back_btn.setStatusTip("Voltar para a página anterior (Alt+Left)")
        back_btn.triggered.connect(self.back_browser)
        toolbar.addAction(back_btn)
        
        # Botão de avançar
        forward_btn = QAction("→", self)
        forward_btn.setStatusTip("Avançar para a próxima página (Alt+Right)")
        forward_btn.triggered.connect(self.forward_browser)
        toolbar.addAction(forward_btn)
        
        # Botão de recarregar
        reload_btn = QAction("↻", self)
        reload_btn.setStatusTip("Recarregar página atual (Ctrl+R)")
        reload_btn.triggered.connect(self.reload_browser)
        toolbar.addAction(reload_btn)
        
        # Botão de home
        home_btn = QAction("🏠", self)
        home_btn.setStatusTip("Ir para a página inicial (Alt+Home)")
        home_btn.triggered.connect(self.home)
        toolbar.addAction(home_btn)
        
        # Adicionar separador
        toolbar.addSeparator()
        
        # Barra de endereço
        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("font-size: 14px; padding: 4px;")
        self.url_bar.setPlaceholderText("Digite um endereço web...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        # Botão de favoritos
        bookmark_btn = QAction("⭐", self)
        bookmark_btn.setStatusTip("Adicionar aos favoritos (Ctrl+D)")
        bookmark_btn.triggered.connect(self.add_bookmark)
        toolbar.addAction(bookmark_btn)
        
        # Botão de nova aba
        new_tab_btn = QAction("+", self)
        new_tab_btn.setStatusTip("Abrir nova aba (Ctrl+T)")
        new_tab_btn.triggered.connect(self.add_new_tab)
        toolbar.addAction(new_tab_btn)
        
        # Adicionar botão de configurações
        settings_btn = QAction("⚙️", self)
        settings_btn.setStatusTip("Configurações (Ctrl+,)")
        settings_btn.triggered.connect(self.show_settings)
        toolbar.addAction(settings_btn)
        
        # Adicionar controles de zoom
        zoom_out_btn = QAction("🔍-", self)
        zoom_out_btn.setStatusTip("Diminuir zoom (Ctrl+-)")
        zoom_out_btn.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        toolbar.addWidget(self.zoom_label)
        
        zoom_in_btn = QAction("🔍+", self)
        zoom_in_btn.setStatusTip("Aumentar zoom (Ctrl++)")
        zoom_in_btn.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_btn)
        
        toolbar.addSeparator()
        
        # Menu de favoritos
        bookmarks_toolbar = QToolBar("Favoritos")
        bookmarks_toolbar.setMovable(False)
        self.addToolBar(bookmarks_toolbar)
        
        bookmarks_label = QLabel("Favoritos:")
        bookmarks_toolbar.addWidget(bookmarks_label)
        
        # Combobox para favoritos
        self.bookmarks_combo = QComboBox()
        self.bookmarks_combo.setMinimumWidth(200)
        self.bookmarks_combo.activated.connect(self.open_bookmark)
        self.update_bookmarks_menu()
        bookmarks_toolbar.addWidget(self.bookmarks_combo)
        
        manage_bookmarks_btn = QPushButton("Gerenciar")
        manage_bookmarks_btn.clicked.connect(self.manage_bookmarks)
        bookmarks_toolbar.addWidget(manage_bookmarks_btn)
        
        # Adicionar botão de downloads
        downloads_btn = QAction("⬇️", self)
        downloads_btn.setStatusTip("Ver Downloads (Ctrl+J)")
        downloads_btn.triggered.connect(self.show_downloads)
        toolbar.addAction(downloads_btn)
        
        # Botão de extensões - Atualizar este trecho
        extensions_btn = QAction("🧩", self)
        extensions_btn.setStatusTip("Gerenciar Extensões")
        extensions_btn.triggered.connect(self.show_extensions)  # Conectar ao método correto
        toolbar.addAction(extensions_btn)
        
        # Adicionar botão de sincronização
        sync_btn = QAction("🔄", self)
        sync_btn.setStatusTip("Sincronizar dados")
        sync_btn.triggered.connect(self.sync_data)
        toolbar.addAction(sync_btn)
        
        # Adicionar botão de modo zen
        zen_btn = QAction("🧘 Modo Zen", self)
        zen_btn.setStatusTip("Ativar/Desativar modo zen")
        zen_btn.setCheckable(True)
        zen_btn.triggered.connect(self.toggle_zen_mode)
        toolbar.addAction(zen_btn)

        # Configuração do modo zen com animações
        self.zen_mode = False
        self.toolbars_visible = True
        self.toolbars = []
        self.toolbars_height = 0
        
        # Definir hide_timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.animate_hide_toolbars)

        # Área sensível com efeito de fade
        self.hover_area = QWidget(self)
        self.hover_area.setFixedHeight(5)  # Mais fino e discreto
        self.hover_area.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(128, 128, 128, 50),
                    stop:1 rgba(128, 128, 128, 0));
            }
        """)
        self.hover_area.hide()
        self.hover_area.enterEvent = lambda e: self.animate_show_toolbars()
        
        # Armazenar barras e criar animações
        self.toolbars = [self.menuBar()] + self.findChildren(QToolBar)
        self.animations = {}
        
        for toolbar in self.toolbars:
            anim = QPropertyAnimation(toolbar, b"pos")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animations[toolbar] = anim
        
        # Grupo de animações para sincronização
        self.animation_group = QParallelAnimationGroup()

        # Criar gerenciador de downloads
        self.download_manager = DownloadManager(self)
        QWebEngineProfile.defaultProfile().downloadRequested.connect(
            self.download_manager.handle_download)
        
        # Criar barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Criar barra de menu
        menubar = self.menuBar()
        
        # Create extensions menu first
        self.extensions_menu = menubar.addMenu("Extensões")
        manage_extensions_action = self.extensions_menu.addAction("Gerenciar Extensões")
        manage_extensions_action.triggered.connect(self.show_extensions)
        self.extensions_menu.addSeparator()
        
        # Initialize extension manager after menu is created
        self.extension_manager = ExtensionManager(self)
        
        # Rest of menus
        file_menu = menubar.addMenu("Arquivo")
        view_menu = menubar.addMenu("Visualizar")
        history_menu = menubar.addMenu("Histórico")
        tools_menu = menubar.addMenu("Ferramentas")
        help_menu = menubar.addMenu("Ajuda")
        
        new_tab_action = file_menu.addAction("Nova Aba")
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(self.add_new_tab)
        
        close_tab_action = file_menu.addAction("Fechar Aba")
        close_tab_action.setShortcut("Ctrl+W")
        close_tab_action.triggered.connect(self.close_current_tab)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Sair")
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        
        fullscreen_action = view_menu.addAction("Modo Tela Cheia")
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
        zoom_in_action = view_menu.addAction("Aumentar Zoom")
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        
        zoom_out_action = view_menu.addAction("Diminuir Zoom")
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        
        reset_zoom_action = view_menu.addAction("Restaurar Zoom")
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.zoom_reset)
        
        show_history_action = history_menu.addAction("Mostrar Histórico")
        show_history_action.setShortcut("Ctrl+H")
        show_history_action.triggered.connect(self.show_history)
        
        clear_history_action = history_menu.addAction("Limpar Histórico")
        settings_action = tools_menu.addAction("Configurações")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        
        keyboard_shortcuts = help_menu.addAction("Atalhos de Teclado")
        keyboard_shortcuts.triggered.connect(self.show_shortcuts)
        
        gestures_help = help_menu.addAction("Ajuda de Gestos")
        gestures_help.triggered.connect(self.show_gestures_help)
        
        about_action = help_menu.addAction("Sobre")
        about_action.triggered.connect(self.show_about)
        
        # Configurar atalhos de teclado
        self.setup_shortcuts()
        
        # Mostrar a janela e adicionar uma aba inicial
        self.add_new_tab()
        self.show()
    
    def setup_shortcuts(self):
        """Configura os atalhos de teclado"""
        # Nova aba
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.add_new_tab)
        
        # Fechar aba
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.close_current_tab)
        
        # Recarregar
        reload_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        reload_shortcut.activated.connect(self.reload_browser)
        
        # Ir para a Home
        home_shortcut = QShortcut(QKeySequence("Alt+Home"), self)
        home_shortcut.activated.connect(self.home)
        
        # Adicionar aos favoritos
        bookmark_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        bookmark_shortcut.activated.connect(self.add_bookmark)
        
        # Voltar
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self.back_browser)
        
        # Avançar
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self.forward_browser)
        
        # Atalho para configurações
        settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut.activated.connect(self.show_settings)
        
        # Atalhos de zoom
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self.zoom_in)
        
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self.zoom_out)
        
        zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        zoom_reset_shortcut.activated.connect(self.zoom_reset)
        
        # Atalho para busca na página
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.find_in_page)
        
        # Atalho para tela cheia
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        
        # Atalho para histórico
        history_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        history_shortcut.activated.connect(self.show_history)
        
        # Atalho para modo leitura
        reader_shortcut = QShortcut(QKeySequence("F5"), self)
        reader_shortcut.activated.connect(self.toggle_reader_mode)
        
        # Atalho para captura de tela
        screenshot_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        screenshot_shortcut.activated.connect(self.capture_visible)
    
    def show_settings(self):
        """Mostra o diálogo de configurações"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_settings()
    
    def apply_settings(self):
        """Aplica as configurações atuais"""
        # Atualizar aparência
        show_status = settings.get("appearance", "show_status_bar")
        self.statusBar().setVisible(show_status)
        
        # Atualizar fonte
        font_size = settings.get("appearance", "font_size")
        self.url_bar.setStyleSheet(f"font-size: {font_size}px; padding: 4px;")
        
        # Atualizar proxy se necessário
        if settings.get("advanced", "proxy_enabled"):
            # Implementar configuração de proxy
            pass
        
        # Aplicar tema
        theme = settings.get("appearance", "theme")
        apply_theme(QApplication.instance(), theme)
        
        # Atualizar configurações de privacidade
        self.privacy_interceptor.do_not_track = settings.get("privacy", "do_not_track")
        self.privacy_interceptor.block_ads = settings.get("privacy", "block_ads")
        ua = settings.get("advanced", "user_agent")
        if ua:
            QWebEngineProfile.defaultProfile().setHttpUserAgent(ua)
    
    def closeEvent(self, event):
        """Limpa dados sensíveis ao fechar se a opção 'clear_on_exit' estiver ativada"""
        if settings.get("privacy", "clear_on_exit"):
            profile = QWebEngineProfile.defaultProfile()
            profile.clearHttpCache()
            profile.cookieStore().deleteAllCookies()
        event.accept()
    
    def load_bookmarks(self):
        """Carrega os favoritos do arquivo"""
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar favoritos: {e}")
        return []
    
    def save_bookmarks(self):
        """Salva os favoritos no arquivo"""
        try:
            with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar favoritos: {e}")
    
    def update_bookmarks_menu(self):
        """Atualiza o menu de favoritos"""
        self.bookmarks_combo.clear()
        self.bookmarks_combo.addItem("Selecione um favorito...")
        
        for bookmark in self.bookmarks:
            self.bookmarks_combo.addItem(bookmark["title"])
    
    def open_bookmark(self, index):
        """Abre o favorito selecionado"""
        if index > 0:  # Ignora o item "Selecione um favorito..."
            bookmark = self.bookmarks[index - 1]
            browser = self.current_browser()
            if browser:
                browser.setUrl(QUrl(bookmark["url"]))
            
            # Reseta o combobox para o primeiro item
            self.bookmarks_combo.setCurrentIndex(0)
    
    def add_bookmark(self):
        """Adiciona a página atual aos favoritos"""
        browser = self.current_browser()
        if not browser:
            return
            
        current_url = browser.url().toString()
        current_title = browser.page().title()
        
        # Verifica se já existe um favorito com essa URL
        for bookmark in self.bookmarks:
            if bookmark["url"] == current_url:
                QMessageBox.information(self, "Favorito Existente", 
                                      "Esta página já está nos seus favoritos.")
                return
        
        # Exibe diálogo para editar o favorito
        dialog = BookmarkDialog(self, current_title, current_url)
        if dialog.exec():
            bookmark_data = dialog.get_data()
            self.bookmarks.append(bookmark_data)
            self.save_bookmarks()
            self.update_bookmarks_menu()
            self.status_bar.showMessage(f"Favorito '{bookmark_data['title']}' adicionado", 3000)
    
    def manage_bookmarks(self):
        """Gerencia os favoritos"""
        # Aqui seria implementado um diálogo mais completo para gestão de favoritos
        # Por enquanto, apenas mostra uma mensagem
        QMessageBox.information(self, "Gerenciar Favoritos", 
                              "Funcionalidade em desenvolvimento.\n\n" +
                              f"Você tem {len(self.bookmarks)} favoritos salvos.")
    
    def add_new_tab(self, url=None):
        """Adiciona uma nova aba ao navegador"""
        tab = BrowserTab(self)
        
        if url:
            tab.browser.setUrl(QUrl(url))
        
        # Conecta os sinais da aba
        tab.browser.urlChanged.connect(lambda qurl, browser=tab.browser: 
                                      self.update_url(qurl, browser))
        tab.browser.loadFinished.connect(lambda _, browser=tab.browser:
                                        self.update_title(browser))
        tab.browser.loadProgress.connect(self.loading_progress)
        
        # Adiciona a aba ao widget de abas
        index = self.tabs.addTab(tab, "Nova Aba")
        self.tabs.setCurrentIndex(index)
        
        # Adicionar entrada ao histórico quando a página carregar
        tab.browser.loadFinished.connect(
            lambda ok, browser=tab.browser: self.add_to_history(browser) if ok else None
        )
        
        # Foca na barra de URL
        self.url_bar.selectAll()
        self.url_bar.setFocus()
    
    def close_current_tab(self):
        """Fecha a aba atual"""
        self.close_tab(self.tabs.currentIndex())
    
    def tab_changed(self, index):
        """Atualiza a interface quando a aba ativa muda"""
        if index >= 0:
            tab = self.tabs.widget(index)
            qurl = tab.browser.url()
            self.update_url(qurl, tab.browser)
            self.update_title(tab.browser)
    
    def close_tab(self, index):
        """Fecha uma aba"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            # Se é a última aba, não feche, apenas limpe
            self.tabs.widget(0).browser.setUrl(QUrl("https://www.google.com"))
    
    def update_url(self, url, browser=None):
        """Atualiza a URL na barra de endereço"""
        if browser == self.tabs.currentWidget().browser:
            self.url_bar.setText(url.toString())
    
    def update_title(self, browser=None):
        """Atualiza o título da aba com o título da página"""
        if browser:
            index = self.get_tab_index(browser)
            if index >= 0:
                title = browser.page().title()
                if len(title) > 20:
                    title = title[:17] + "..."
                
                if not title:
                    title = "Nova Aba"
                    
                self.tabs.setTabText(index, title)
                if browser == self.tabs.currentWidget().browser:
                    self.setWindowTitle(f"{title} - Meu Navegador")
    
    def get_tab_index(self, browser):
        """Encontra o índice da aba que contém o navegador especificado"""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.browser == browser:
                return i
        return -1
    
    def loading_progress(self, progress):
        """Atualiza a barra de status com o progresso de carregamento"""
        if progress < 100:
            self.status_bar.showMessage(f"Carregando... {progress}%")
        else:
            self.status_bar.showMessage("Pronto")
    
    def current_browser(self):
        """Retorna o objeto QWebEngineView da aba atual"""
        return self.tabs.currentWidget().browser if self.tabs.count() > 0 else None
    
    def navigate_to_url(self):
        """Navega para a URL digitada na barra de endereço"""
        browser = self.current_browser()
        if not browser:
            return
            
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        browser.setUrl(QUrl(url))
    
    def back_browser(self):
        """Volta para a página anterior na aba atual"""
        browser = self.current_browser()
        if browser:
            browser.back()
    
    def forward_browser(self):
        """Avança para a próxima página na aba atual"""
        browser = self.current_browser()
        if browser:
            browser.forward()
    
    def reload_browser(self):
        """Recarrega a página atual"""
        browser = self.current_browser()
        if browser:
            browser.reload()
    
    def home(self):
        """Vai para a página inicial configurada"""
        browser = self.current_browser()
        if browser:
            home_page = settings.get("general", "home_page")
            browser.setUrl(QUrl(home_page))
    
    def zoom_in(self):
        browser = self.current_browser()
        if browser:
            current_zoom = browser.zoomFactor()
            browser.setZoomFactor(current_zoom + 0.1)
            self.zoom_label.setText(f"{int(current_zoom * 110)}%")
    
    def zoom_out(self):
        browser = self.current_browser()
        if browser:
            current_zoom = browser.zoomFactor()
            browser.setZoomFactor(max(0.25, current_zoom - 0.1))
            self.zoom_label.setText(f"{int(current_zoom * 90)}%")
    
    def zoom_reset(self):
        browser = self.current_browser()
        if browser:
            browser.setZoomFactor(1.0)
            self.zoom_label.setText("100%")
    
    def contextMenuEvent(self, event):
        """Manipula eventos de menu de contexto (clique direito)"""
        browser = self.current_browser()
        if browser:
            menu = QMenu(self)
            
            back_action = menu.addAction("Voltar")
            back_action.triggered.connect(browser.back)
            
            forward_action = menu.addAction("Avançar")
            forward_action.triggered.connect(browser.forward)
            
            reload_action = menu.addAction("Recarregar")
            reload_action.triggered.connect(browser.reload)
            
            menu.addSeparator()
            
            new_tab_action = menu.addAction("Nova Aba")
            new_tab_action.triggered.connect(self.add_new_tab)
            
            close_tab_action = menu.addAction("Fechar Aba")
            close_tab_action.triggered.connect(self.close_current_tab)
            
            menu.addSeparator()
            
            bookmark_action = menu.addAction("Adicionar aos Favoritos")
            bookmark_action.triggered.connect(self.add_bookmark)
            
            menu.exec(event.globalPosition().toPoint())
    
    # Novos métodos para funcionalidades adicionais
    def find_in_page(self):
        """Abre o painel de busca na página atual"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.show_search_panel()
    
    def toggle_reader_mode(self):
        """Alterna o modo de leitura na aba atual"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.toggle_reader_mode()
    
    def capture_visible(self):
        """Captura a área visível da página atual"""
        browser = self.current_browser()
        if browser:
            pixmap = ScreenshotTool.capture_visible(browser)
            dialog = ScreenshotDialog(self, pixmap)
            dialog.exec()
    
    def capture_full_page(self):
        """Captura a página inteira"""
        browser = self.current_browser()
        if browser:
            pixmap = ScreenshotTool.capture_full_page(browser)
            dialog = ScreenshotDialog(self, pixmap)
            dialog.exec()
    
    def show_shortcuts(self):
        """Mostra os atalhos de teclado disponíveis"""
        shortcuts = """
        <h2>Atalhos de Teclado</h2>
        <table>
            <tr><th>Atalho</th><th>Função</th></tr>
            <tr><td>Ctrl+T</td><td>Nova Aba</td></tr>
            <tr><td>Ctrl+W</td><td>Fechar Aba</td></tr>
            <tr><td>Ctrl+R</td><td>Recarregar Página</td></tr>
            <tr><td>Ctrl+F</td><td>Buscar na Página</td></tr>
            <tr><td>Ctrl+D</td><td>Adicionar aos Favoritos</td></tr>
            <tr><td>F5</td><td>Modo Leitura</td></tr>
            <tr><td>F11</td><td>Tela Cheia</td></tr>
            <tr><td>Ctrl+Shift+S</td><td>Captura de Tela</td></tr>
            <tr><td>Alt+Left</td><td>Voltar</td></tr>
            <tr><td>Alt+Right</td><td>Avançar</td></tr>
            <tr><td>Ctrl+H</td><td>Histórico</td></tr>
            <tr><td>Ctrl+,</td><td>Configurações</td></tr>
        </table>
        """
        QMessageBox.information(self, "Atalhos de Teclado", shortcuts)
    
    def show_gestures_help(self):
        """Mostra ajuda sobre gestos do mouse"""
        help_text = """
        <h2>Gestos do Mouse</h2>
        <p>Use o botão direito do mouse para desenhar gestos:</p>
        <ul>
            <li><b>Arraste para esquerda</b>: Voltar</li>
            <li><b>Arraste para direita</b>: Avançar</li>
            <li><b>Arraste para cima</b>: Recarregar</li>
            <li><b>Arraste para baixo</b>: Fechar aba</li>
        </ul>
        """
        QMessageBox.information(self, "Ajuda de Gestos", help_text)
    
    def show_about(self):
        """Mostra informações sobre o navegador"""
        about_text = """
        <h1>Meu Navegador</h1>
        <p>Versão 1.5.0</p>
        <p>Um navegador web moderno desenvolvido com Python e PyQt6.</p>
        <p>Recursos:</p>
        <ul>
            <li>Navegação em abas</li>
            <li>Favoritos</li>
            <li>Histórico</li>
            <li>Pesquisa na página</li>
            <li>Modo leitura</li>
            <li>Gestos de mouse</li>
            <li>Captura de tela</li>
            <li>Temas personalizáveis</li>
        </ul>
        <p>&copy; 2023</p>
        """
        QMessageBox.about(self, "Sobre", about_text)
    
    def show_history(self):
        """Exibe o diálogo de histórico de navegação"""
        dialog = HistoryDialog(self, self.history_manager)
        dialog.exec()
    
    def clear_history(self):
        """Limpa o histórico de navegação"""
        self.history_manager.clear_history()
        self.status_bar.showMessage("Histórico limpo", 3000)
    
    def add_to_history(self, browser):
        """Adiciona a página atual ao histórico"""
        url = browser.url().toString()
        title = browser.page().title() or url
        
        if url.startswith(("http://", "https://")):
            self.history_manager.add_entry(url, title)
    
    def toggle_fullscreen(self):
        """Alterna entre modo de tela cheia e normal"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_downloads(self):
        """Mostra o diálogo de downloads"""
        if hasattr(self, 'download_manager'):
            self.download_manager.show_downloads_dialog()
    
    def show_extensions(self):
        """Mostra o gerenciador de extensões"""
        if hasattr(self, 'extension_manager'):
            self.extension_manager.show_manager_dialog()
    
    def manage_extensions(self):
        """Redireciona para show_extensions para manter compatibilidade"""
        self.show_extensions()
    
    def sync_data(self):
        """Sincroniza dados do navegador"""
        try:
            from sync_manager import SyncManager
            if not hasattr(self, 'sync_manager'):
                self.sync_manager = SyncManager(self)
            self.sync_manager.sync_all_data()
        except Exception as e:
            QMessageBox.warning(self, "Erro de Sincronização",
                              f"Não foi possível sincronizar: {str(e)}")
    
    def add_extension_action(self, action):
        """Adiciona ação de extensão ao menu"""
        if hasattr(self, 'extensions_menu'):  # Safety check
            self.extensions_menu.addAction(action)

    def toggle_zen_mode(self, enabled):
        """Ativa/desativa o modo zen"""
        self.zen_mode = enabled
        
        if enabled:
            self.toolbars = [self.menuBar()] + self.findChildren(QToolBar)
            self.toolbars_height = sum(t.height() for t in self.toolbars)
            self.animate_hide_toolbars()
            self.hover_area.show()
            self.hover_area.raise_()
            self.tabs.setContentsMargins(0, 5, 0, 0)
        else:
            self.animate_show_toolbars()
            self.hover_area.hide()
            self.tabs.setContentsMargins(0, 0, 0, 0)
            self.toolbars = []
        
        self.update_zen_geometry()

    def animate_hide_toolbars(self):
        """Esconde as barras com animação"""
        if not self.zen_mode or not self.toolbars_visible:
            return
        
        self.animation_group.stop()
        self.animation_group.clear()
        
        for i, toolbar in enumerate(self.toolbars):
            anim = QPropertyAnimation(toolbar, b"pos", self)
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(toolbar.pos())
            anim.setEndValue(QPoint(toolbar.x(), -toolbar.height()))
            self.animation_group.addAnimation(anim)
        
        self.toolbars_visible = False
        self.animation_group.start()

    def animate_show_toolbars(self):
        """Mostra as barras com animação"""
        if not self.zen_mode or self.toolbars_visible:
            return
            
        self.animation_group.stop()
        self.animation_group.clear()
        
        # Mostrar todas as barras antes de animar
        for toolbar in self.toolbars:
            toolbar.show()
        
        current_y = 0
        for toolbar in self.toolbars:
            anim = QPropertyAnimation(toolbar, b"pos", self)
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(QPoint(toolbar.x(), -toolbar.height()))
            anim.setEndValue(QPoint(toolbar.x(), current_y))
            current_y += toolbar.height()
            self.animation_group.addAnimation(anim)
        
        self.toolbars_visible = True
        self.animation_group.start()

    def _on_hover_enter(self, event):
        """Handler seguro para evento de hover"""
        if self.zen_mode and not self.toolbars_visible:
            self.animate_show_toolbars()

    def _on_animation_finished(self):
        """Handler para fim da animação"""
        if not self.toolbars_visible:
            for toolbar in self.toolbars:
                toolbar.hide()
        else:
            self.hide_timer.start(3000)  # Auto-hide após 3 segundos

    def update_zen_geometry(self):
        """Atualiza o layout do modo zen"""
        if self.zen_mode:
            self.hover_area.setGeometry(0, 0, self.width(), 5)
            
            if not self.toolbars_visible:
                self.tabs.setContentsMargins(0, 5, 0, 0)
            else:
                self.tabs.setContentsMargins(0, 0, 0, 0)

    def resizeEvent(self, event):
        """Quando a janela é redimensionada"""
        super().resizeEvent(event)
        self.update_zen_geometry()
    
    def enterEvent(self, event):
        """Quando o mouse entra na janela"""
        super().enterEvent(event)
        if self.zen_mode:
            self.hide_timer.stop()
    
    def leaveEvent(self, event):
        """Quando o mouse sai da janela"""
        super().leaveEvent(event)
        if self.zen_mode and self.toolbars_visible:
            self.hide_timer.start(1000)

if __name__ == "__main__":
    # Desativar mensagens de console de WebEngine
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-logging"
    
    app = QApplication(sys.argv)
    
    # Aplicar tema inicial
    theme = settings.get("appearance", "theme")
    apply_theme(app, theme)
    
    window = SimpleBrowser()
    sys.exit(app.exec())


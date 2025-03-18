from PyQt6.QtWidgets import (QDialog, QTabWidget, QVBoxLayout, QFormLayout,
                           QLineEdit, QCheckBox, QComboBox, QPushButton,
                           QFileDialog, QSpinBox, QLabel, QWidget, QHBoxLayout)
from config.settings import settings  # Import the settings instance
from ui.themes import THEMES

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Criar tabs para diferentes seções
        tabs = QTabWidget()
        tabs.addTab(self.create_general_tab(), "Geral")
        tabs.addTab(self.create_privacy_tab(), "Privacidade")
        tabs.addTab(self.create_appearance_tab(), "Aparência")
        tabs.addTab(self.create_advanced_tab(), "Avançado")
        
        layout.addWidget(tabs)
        
        # Botões
        buttons_layout = QHBoxLayout()
        apply_button = QPushButton("Aplicar")
        apply_button.clicked.connect(self.apply_settings)
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(apply_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        self.home_page = QLineEdit(settings.get("general", "home_page"))
        layout.addRow("Página inicial:", self.home_page)
        
        self.download_path = QLineEdit(settings.get("general", "download_path"))
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self.choose_download_path)
        download_layout = QHBoxLayout()
        download_layout.addWidget(self.download_path)
        download_layout.addWidget(browse_btn)
        layout.addRow("Local de download:", download_layout)
        
        self.save_session = QCheckBox()
        self.save_session.setChecked(settings.get("general", "save_session"))
        layout.addRow("Salvar sessão:", self.save_session)
        
        widget.setLayout(layout)
        return widget
    
    def create_privacy_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        self.clear_on_exit = QCheckBox()
        self.clear_on_exit.setChecked(settings.get("privacy", "clear_on_exit"))
        layout.addRow("Limpar dados ao sair:", self.clear_on_exit)
        
        self.do_not_track = QCheckBox()
        self.do_not_track.setChecked(settings.get("privacy", "do_not_track"))
        layout.addRow("Enviar sinal 'Não Rastrear':", self.do_not_track)
        
        self.block_ads = QCheckBox()
        self.block_ads.setChecked(settings.get("privacy", "block_ads"))
        layout.addRow("Bloquear anúncios (experimental):", self.block_ads)
        
        widget.setLayout(layout)
        return widget
    
    def create_appearance_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        self.theme = QComboBox()
        self.theme.addItems(list(THEMES.keys()))  # Usar temas disponíveis
        self.theme.setCurrentText(settings.get("appearance", "theme"))
        layout.addRow("Tema:", self.theme)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(settings.get("appearance", "font_size"))
        layout.addRow("Tamanho da fonte:", self.font_size)
        
        self.show_bookmarks_bar = QCheckBox()
        self.show_bookmarks_bar.setChecked(settings.get("appearance", "show_bookmarks_bar"))
        layout.addRow("Mostrar barra de favoritos:", self.show_bookmarks_bar)
        
        self.show_status_bar = QCheckBox()
        self.show_status_bar.setChecked(settings.get("appearance", "show_status_bar"))
        layout.addRow("Mostrar barra de status:", self.show_status_bar)
        
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        self.hardware_acceleration = QCheckBox()
        self.hardware_acceleration.setChecked(settings.get("advanced", "hardware_acceleration"))
        layout.addRow("Aceleração por hardware:", self.hardware_acceleration)
        
        self.proxy_enabled = QCheckBox()
        self.proxy_enabled.setChecked(settings.get("advanced", "proxy_enabled"))
        layout.addRow("Usar proxy:", self.proxy_enabled)
        
        proxy_layout = QHBoxLayout()
        self.proxy_address = QLineEdit(settings.get("advanced", "proxy_address"))
        self.proxy_port = QLineEdit(settings.get("advanced", "proxy_port"))
        proxy_layout.addWidget(self.proxy_address)
        proxy_layout.addWidget(QLabel(":"))
        proxy_layout.addWidget(self.proxy_port)
        layout.addRow("Endereço do proxy:", proxy_layout)
        
        self.user_agent = QLineEdit(settings.get("advanced", "user_agent"))
        layout.addRow("User Agent personalizado:", self.user_agent)
        
        widget.setLayout(layout)
        return widget
    
    def save_settings(self):
        # Salvar configurações gerais
        settings.set("general", "home_page", self.home_page.text())
        settings.set("general", "download_path", self.download_path.text())
        settings.set("general", "save_session", self.save_session.isChecked())
        
        # Salvar configurações de privacidade
        settings.set("privacy", "clear_on_exit", self.clear_on_exit.isChecked())
        settings.set("privacy", "do_not_track", self.do_not_track.isChecked())
        settings.set("privacy", "block_ads", self.block_ads.isChecked())
        
        # Salvar configurações de aparência
        settings.set("appearance", "theme", self.theme.currentText())
        settings.set("appearance", "font_size", self.font_size.value())
        settings.set("appearance", "show_bookmarks_bar", self.show_bookmarks_bar.isChecked())
        settings.set("appearance", "show_status_bar", self.show_status_bar.isChecked())
        
        # Salvar configurações avançadas
        settings.set("advanced", "hardware_acceleration", self.hardware_acceleration.isChecked())
        settings.set("advanced", "proxy_enabled", self.proxy_enabled.isChecked())
        settings.set("advanced", "proxy_address", self.proxy_address.text())
        settings.set("advanced", "proxy_port", self.proxy_port.text())
        settings.set("advanced", "user_agent", self.user_agent.text())
        
        settings.save_settings()
        self.accept()
    
    def apply_settings(self):
        """Aplica as configurações sem fechar o diálogo"""
        self.save_settings()
        if self.parent():
            self.parent().apply_settings()
    
    def choose_download_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Escolher pasta de download",
            settings.get("general", "download_path")
        )
        if path:
            self.download_path.setText(path)

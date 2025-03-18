from PyQt6.QtGui import QAction  # Add this import
from extensions.extension_base import ExtensionBase

class Extension(ExtensionBase):
    def _init(self):  # Mudado de init para _init
        self.create_action("🌙 Modo Escuro", self.toggle_dark_mode)
        self.dark_mode_enabled = False
        
    def toggle_dark_mode(self):
        self.dark_mode_enabled = not self.dark_mode_enabled
        current_tab = self.browser.current_browser()
        if current_tab:
            js = """
            if (!document.getElementById('dark-mode-style')) {
                var style = document.createElement('style');
                style.id = 'dark-mode-style';
                style.innerHTML = 'body { background-color: #1a1a1a !important; color: #ffffff !important; }';
                document.head.appendChild(style);
            } else {
                var style = document.getElementById('dark-mode-style');
                style.parentNode.removeChild(style);
            }
            """
            current_tab.page().runJavaScript(js)

from PyQt6.QtGui import QAction  # Changed from QtWidgets to QtGui
from abc import ABC, abstractmethod

class ExtensionBase(ABC):
    """Classe base para extensões"""
    
    def __init__(self, browser):
        self.browser = browser
        self.actions = []
    
    def init(self):
        """Inicializa a extensão"""
        print(f"Inicializando extensão: {self.__class__.__name__}")
        self._init()  # Chama o método de inicialização real
    
    @abstractmethod
    def _init(self):
        """Método real de inicialização a ser implementado pelas extensões"""
        pass
    
    def enable(self):
        """Ativa a extensão"""
        pass
    
    def disable(self):
        """Desativa a extensão"""
        pass
    
    def get_actions(self):
        """Retorna ações para o menu de extensões"""
        return self.actions
    
    def create_action(self, name, callback, shortcut=None):
        """Helper para criar ações"""
        action = QAction(name, self.browser)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.actions.append(action)
        return action

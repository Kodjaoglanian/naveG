from PyQt6.QtCore import QObject, QEvent, QPoint, QTimer, Qt, pyqtSignal  # Added QObject here
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget

class GestureHandler(QObject):
    """Gerenciador de gestos de mouse"""
    
    THRESHOLD = 50  # Distância mínima para considerar um gesto
    
    def __init__(self, browser_tab):
        super().__init__()  # Initialize QObject
        self.browser_tab = browser_tab
        self.tracking = False
        self.start_pos = QPoint()
        self.last_pos = QPoint()
        self.path = []
        
        # Configurar temporizador para limpar o rastro
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clear_gesture)
        
        # Conectar eventos de mouse
        self.browser_tab.browser.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filtra eventos para capturar gestos do mouse"""
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.RightButton:
            self.start_gesture(event.position().toPoint())
            return True
        
        elif event.type() == QEvent.Type.MouseMove and self.tracking:
            self.update_gesture(event.position().toPoint())
            return True
        
        elif event.type() == QEvent.Type.MouseButtonRelease and self.tracking and event.button() == Qt.MouseButton.RightButton:
            self.end_gesture(event.position().toPoint())
            return True
        
        return False
    
    def start_gesture(self, pos):
        """Inicia o rastreamento de um gesto"""
        self.tracking = True
        self.start_pos = pos
        self.last_pos = pos
        self.path = [pos]
        self.browser_tab.setMouseTracking(True)
    
    def update_gesture(self, pos):
        """Atualiza o caminho do gesto"""
        self.last_pos = pos
        self.path.append(pos)
        self.browser_tab.update()  # Força redesenho para mostrar o gesto
    
    def end_gesture(self, pos):
        """Finaliza e processa o gesto"""
        self.tracking = False
        self.path.append(pos)
        
        dx = pos.x() - self.start_pos.x()
        dy = pos.y() - self.start_pos.y()
        
        # Detectar direção do gesto
        if abs(dx) > self.THRESHOLD or abs(dy) > self.THRESHOLD:
            if abs(dx) > abs(dy):  # Horizontal
                if dx > 0:
                    self.process_gesture("right")
                else:
                    self.process_gesture("left")
            else:  # Vertical
                if dy > 0:
                    self.process_gesture("down")
                else:
                    self.process_gesture("up")
        
        # Começar temporizador para limpar o traço
        self.timer.start(500)  # Desaparece após 500ms
    
    def clear_gesture(self):
        """Limpa o rastro do gesto"""
        self.path = []
        self.browser_tab.update()
    
    def process_gesture(self, direction):
        """Processa um gesto reconhecido"""
        if direction == "left":
            self.browser_tab.browser.back()
        elif direction == "right":
            self.browser_tab.browser.forward()
        elif direction == "up":
            self.browser_tab.browser.reload()
        elif direction == "down":
            self.browser_tab.parent().close_current_tab()
    
    def draw_gesture_path(self, painter):
        """Desenha o caminho do gesto na tela"""
        if not self.path or len(self.path) < 2:
            return
        
        pen = QPen(QColor(0, 120, 215, 150))
        pen.setWidth(4)
        painter.setPen(pen)
        
        for i in range(1, len(self.path)):
            painter.drawLine(self.path[i-1], self.path[i])


class GestureAwareWebView(QWidget):
    """Widget que adiciona suporte a gestos para o navegador"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Removed automatic initialization of GestureHandler:
        # self.gesture_handler = GestureHandler(self)
    
    def paintEvent(self, event):
        """Adiciona suporte para desenhar o caminho do gesto"""
        super().paintEvent(event)
        # Draw gesture path if parent's gesture_handler exists and has data.
        if hasattr(self.parent, "gesture_handler") and self.parent.gesture_handler.path:
            painter = QPainter(self)
            self.parent.gesture_handler.draw_gesture_path(painter)

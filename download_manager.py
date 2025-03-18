from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
                           QProgressBar, QPushButton, QLabel,
                           QFileDialog, QMessageBox, QHBoxLayout,
                           QWidget)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtGui import QIcon
import os
import humanize

class DownloadItem(QWidget):
    def __init__(self, download, dialog, parent=None):  # Add dialog parameter
        super().__init__(parent)
        self.download = download
        self.dialog = dialog  # Store reference to dialog
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Informações do download
        info_layout = QVBoxLayout()
        self.name_label = QLabel(download.downloadFileName())
        self.name_label.setWordWrap(True)  # Allow text wrapping
        self.status_label = QLabel("Iniciando...")
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.status_label)
        
        # Container vertical para progress bar
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)  # Show percentage
        progress_layout.addWidget(self.progress_bar)
        
        # Botões
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMaximumWidth(100)
        self.cancel_button.clicked.connect(self.cancel_download)
        
        # Adicionar widgets ao layout principal
        layout.addLayout(info_layout, stretch=2)
        layout.addLayout(progress_layout, stretch=1)
        layout.addWidget(self.cancel_button)
        
        # Conectar sinais
        self.download.receivedBytesChanged.connect(self.update_progress)
        self.download.stateChanged.connect(self.handle_state_change)

    def cancel_download(self):
        if self.cancel_button.text() == "Remover":
            self.dialog.remove_item(self)  # Use dialog reference
        else:
            self.download.cancel()
    
    def update_progress(self):
        received = self.download.receivedBytes()
        total = self.download.totalBytes()
        
        if total > 0:
            progress = int((received * 100) / total)
            self.progress_bar.setValue(progress)
            
            received_str = humanize.naturalsize(received)
            total_str = humanize.naturalsize(total)
            self.status_label.setText(f"Baixando: {received_str} de {total_str}")
    
    def handle_state_change(self, state):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.status_label.setText("Concluído")
            self.cancel_button.setText("Remover")
            self.progress_bar.setValue(100)
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self.status_label.setText("Cancelado")
            self.cancel_button.setText("Remover")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self.status_label.setText(f"Erro: {self.download.interruptReasonString()}")
            self.cancel_button.setText("Tentar novamente")

class DownloadsDialog(QDialog):
    def __init__(self, parent, download_manager):
        super().__init__(parent)
        self.download_manager = download_manager
        self.setWindowTitle("Downloads")
        self.setMinimumWidth(700)  # Increased width
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add spacing between elements
        
        # Barra de ferramentas
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 10)  # Add bottom margin
        
        clear_button = QPushButton("Limpar Concluídos")
        clear_button.clicked.connect(self.clear_completed)
        toolbar.addWidget(clear_button)
        
        open_folder = QPushButton("Abrir Pasta Downloads")
        open_folder.clicked.connect(self.open_downloads_folder)
        toolbar.addWidget(open_folder)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Lista de downloads
        self.downloads_list = QListWidget()
        self.downloads_list.setSpacing(5)  # Add spacing between items
        layout.addWidget(self.downloads_list)
        
        self.setLayout(layout)
        self.update_downloads_list()
    
    def update_downloads_list(self):
        """Atualiza lista de downloads"""
        self.downloads_list.clear()
        for download in self.download_manager.downloads:
            item = QListWidgetItem(self.downloads_list)
            widget = DownloadItem(download, self)  # Pass self as dialog
            
            # Set item size
            item.setSizeHint(QSize(self.downloads_list.width(), 80))
            
            self.downloads_list.addItem(item)
            self.downloads_list.setItemWidget(item, widget)
    
    def remove_item(self, download_item):
        """Remove um item específico da lista"""
        for i in range(self.downloads_list.count()):
            item = self.downloads_list.item(i)
            if self.downloads_list.itemWidget(item) == download_item:
                self.download_manager.downloads.remove(download_item.download)
                self.downloads_list.takeItem(i)
                break
    
    def clear_completed(self):
        """Remove downloads concluídos da lista"""
        for i in range(self.downloads_list.count() - 1, -1, -1):
            item = self.downloads_list.item(i)
            widget = self.downloads_list.itemWidget(item)
            if widget.download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self.download_manager.downloads.remove(widget.download)
                self.downloads_list.takeItem(i)
    
    def open_downloads_folder(self):
        """Abre a pasta de downloads no explorador de arquivos"""
        downloads_path = os.path.expanduser("~/Downloads")
        os.startfile(downloads_path)

class DownloadManager:
    def __init__(self, parent):
        self.parent = parent
        self.downloads = []
        self.dialog = None
    
    def handle_download(self, download):
        """Gerencia um novo download"""
        suggested_name = download.suggestedFileName()
        downloads_path = os.path.expanduser("~/Downloads")
        
        # Criar pasta de downloads se não existir
        os.makedirs(downloads_path, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Salvar arquivo",
            os.path.join(downloads_path, suggested_name),
            "Todos os arquivos (*.*)"
        )
        
        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))
            
            self.downloads.append(download)
            download.accept()
            
            # Mostrar notificação
            self.parent.status_bar.showMessage(
                f"Iniciando download: {os.path.basename(file_path)}", 3000)
            
            # Mostrar diálogo de downloads
            self.show_downloads_dialog()
        else:
            download.cancel()
    
    def show_downloads_dialog(self):
        """Mostra diálogo com downloads ativos e concluídos"""
        if not self.dialog:
            self.dialog = DownloadsDialog(self.parent, self)
        elif not self.dialog.isVisible():
            self.dialog.update_downloads_list()
        
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

import os
import json
import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QHeaderView, QLabel, QLineEdit, QMenu)
from PyQt6.QtCore import Qt, QUrl

class HistoryManager:
    def __init__(self, history_file):
        self.history_file = history_file
        self.history = self.load_history()
    
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar histórico: {e}")
                return []
        return []
    
    def save_history(self):
        try:
            # Limitar o histórico a 1000 itens
            if len(self.history) > 1000:
                self.history = self.history[-1000:]
                
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def add_entry(self, url, title):
        timestamp = datetime.datetime.now().isoformat()
        entry = {
            "url": url,
            "title": title,
            "timestamp": timestamp,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(entry)
        self.save_history()
    
    def clear_history(self):
        self.history = []
        self.save_history()
        
    def search_history(self, query):
        """Busca entradas no histórico que contenham o termo de busca"""
        query = query.lower()
        return [
            entry for entry in self.history 
            if query in entry["url"].lower() or query in entry["title"].lower()
        ]
    
    def get_today_entries(self):
        """Retorna entradas de hoje"""
        today = datetime.datetime.now().date()
        return [
            entry for entry in self.history
            if datetime.datetime.fromisoformat(entry["timestamp"]).date() == today
        ]

class HistoryDialog(QDialog):
    def __init__(self, parent, history_manager):
        super().__init__(parent)
        self.parent = parent
        self.history_manager = history_manager
        self.setWindowTitle("Histórico de Navegação")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout()
        
        # Barra de pesquisa
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Digite para pesquisar no histórico")
        self.search_box.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)
        
        # Tabela de histórico
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Título", "URL", "Data"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self.open_url)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)
        
        # Botões
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Limpar Histórico")
        clear_button.clicked.connect(self.clear_history)
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.populate_table(self.history_manager.history)
    
    def populate_table(self, history):
        self.table.setRowCount(0)
        for entry in reversed(history):  # Mostra os mais recentes primeiro
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(entry["url"]))
            self.table.setItem(row, 2, QTableWidgetItem(entry["date"]))
    
    def filter_history(self):
        query = self.search_box.text()
        if query:
            filtered_history = self.history_manager.search_history(query)
            self.populate_table(filtered_history)
        else:
            self.populate_table(self.history_manager.history)
    
    def open_url(self, row, column):
        url = self.table.item(row, 1).text()
        self.parent.add_new_tab(url)
        self.accept()
    
    def clear_history(self):
        self.history_manager.clear_history()
        self.table.setRowCount(0)
    
    def show_context_menu(self, position):
        menu = QMenu()
        open_action = menu.addAction("Abrir em Nova Aba")
        remove_action = menu.addAction("Remover do Histórico")
        
        action = menu.exec(self.table.mapToGlobal(position))
        
        if action == open_action:
            rows = set(index.row() for index in self.table.selectedIndexes())
            for row in rows:
                url = self.table.item(row, 1).text()
                self.parent.add_new_tab(url)
        
        elif action == remove_action:
            rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
            for row in rows:
                url = self.table.item(row, 1).text()
                # Remover do histórico
                self.history_manager.history = [
                    entry for entry in self.history_manager.history 
                    if entry["url"] != url
                ]
                self.table.removeRow(row)
            self.history_manager.save_history()

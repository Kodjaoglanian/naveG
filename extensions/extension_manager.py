import os
import json
import importlib.util
from pathlib import Path
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QTextEdit, QHBoxLayout, QListWidgetItem
from PyQt6.QtCore import Qt

class ExtensionManager:
    def __init__(self, browser):
        self.browser = browser
        self.extensions = {}
        # Usar caminho absoluto baseado no diretório do arquivo atual
        current_dir = Path(__file__).resolve().parent
        self.extension_dir = current_dir / "installed"
        self.extension_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 Diretório de extensões: {self.extension_dir}")
        
        # Debug: Listar arquivos no diretório
        print("\nArquivos encontrados:")
        for item in self.extension_dir.glob("**/*"):
            print(f"  {'📁' if item.is_dir() else '📄'} {item}")
        print()
        
        self.load_extensions()
    
    def load_extensions(self):
        """Carrega todas as extensões instaladas"""
        if not self.extension_dir.exists():
            print(f"❌ Diretório de extensões não encontrado: {self.extension_dir}")
            return

        # Listar todos os diretórios de extensões
        ext_dirs = [d for d in self.extension_dir.iterdir() if d.is_dir()]
        print(f"📦 Encontradas {len(ext_dirs)} possíveis extensões")
        
        for ext_dir in ext_dirs:
            manifest_path = ext_dir / "manifest.json"
            print(f"\nVerificando extensão em: {ext_dir}")
            print(f"Procurando manifest em: {manifest_path}")
            
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    print(f"✅ Manifest carregado: {manifest['name']}")
                    
                    main_file = ext_dir / manifest.get("main", "main.py")
                    print(f"Procurando arquivo principal em: {main_file}")
                    
                    if main_file.exists():
                        self.load_extension(ext_dir.name, main_file, manifest)
                    else:
                        print(f"❌ Arquivo principal não encontrado: {main_file}")
                except Exception as e:
                    print(f"❌ Erro ao carregar extensão {ext_dir.name}:")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ Manifest não encontrado em: {manifest_path}")
    
    def load_extension(self, ext_id, main_file, manifest):
        """Carrega uma extensão específica"""
        try:
            print(f"\n🔌 Carregando extensão: {ext_id}")
            print(f"📄 Arquivo principal: {main_file}")
            print(f"📦 Manifesto: {manifest}")
            
            # Add module directory to Python path
            import sys
            module_dir = os.path.dirname(main_file)
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)
            
            # Carregar módulo dinamicamente
            spec = importlib.util.spec_from_file_location(ext_id, str(main_file))
            if not spec:
                print(f"❌ Não foi possível criar spec para {main_file}")
                return
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[ext_id] = module  # Register the module
            spec.loader.exec_module(module)
            
            # Inicializar extensão
            if hasattr(module, 'Extension'):
                extension = module.Extension(self.browser)
                if hasattr(extension, '_init'):  # Verifica se tem o método _init
                    extension.init()  # Chama o método init que internamente chama _init
                    self.extensions[ext_id] = {
                        'instance': extension,
                        'manifest': manifest,
                        'enabled': True,
                        'actions': extension.get_actions()
                    }
                    
                    # Adicionar ações ao menu
                    actions = extension.get_actions()
                    print(f"✅ Ações carregadas: {len(actions)}")
                    for action in actions:
                        self.browser.add_extension_action(action)
                        action.setEnabled(True)
                    
                    print(f"✅ Extensão {ext_id} carregada com sucesso")
                else:
                    print(f"❌ Método _init não encontrado na extensão {ext_id}")
            else:
                print(f"❌ Classe Extension não encontrada em {ext_id}")
        except Exception as e:
            print(f"❌ Erro ao inicializar extensão {ext_id}:")
            import traceback
            traceback.print_exc()
    
    def show_manager_dialog(self):
        """Mostra diálogo de gerenciamento de extensões"""
        dialog = ExtensionManagerDialog(self.browser, self)
        dialog.exec()
    
    def toggle_extension(self, ext_id):
        """Ativa/desativa uma extensão"""
        if ext_id in self.extensions:
            ext = self.extensions[ext_id]
            ext['enabled'] = not ext['enabled']
            
            # Enable/disable all actions for this extension
            for action in ext['actions']:
                action.setEnabled(ext['enabled'])
            
            # Call enable/disable methods
            if ext['enabled']:
                ext['instance'].enable()
            else:
                ext['instance'].disable()

class ExtensionManagerDialog(QDialog):
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Gerenciador de Extensões")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Lista de extensões
        self.ext_list = QListWidget()
        self.ext_list.itemClicked.connect(self.on_item_clicked)  # Add click handler
        self.update_extension_list()
        layout.addWidget(self.ext_list)
        
        # Container para informações da extensão
        info_layout = QVBoxLayout()
        self.ext_info = QTextEdit()
        self.ext_info.setReadOnly(True)
        self.ext_info.setMaximumHeight(100)
        info_layout.addWidget(self.ext_info)
        layout.addLayout(info_layout)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("Ativar/Desativar")
        self.toggle_btn.clicked.connect(self.toggle_selected)
        self.toggle_btn.setEnabled(False)  # Disabled until selection
        button_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_extension_list(self):
        """Atualiza a lista de extensões"""
        self.ext_list.clear()
        for ext_id, ext in self.manager.extensions.items():
            status = "✅ Ativo" if ext['enabled'] else "❌ Desativado"
            item = QListWidgetItem(f"{ext['manifest']['name']} - {status}")
            item.setData(Qt.ItemDataRole.UserRole, ext_id)  # Store ext_id
            self.ext_list.addItem(item)
    
    def on_item_clicked(self, item):
        ext_id = item.data(Qt.ItemDataRole.UserRole)
        if ext_id in self.manager.extensions:
            ext = self.manager.extensions[ext_id]
            # Show extension info
            info = f"Nome: {ext['manifest']['name']}\n"
            info += f"Versão: {ext['manifest']['version']}\n"
            info += f"Descrição: {ext['manifest'].get('description', 'Sem descrição')}"
            self.ext_info.setText(info)
            self.toggle_btn.setEnabled(True)
    
    def toggle_selected(self):
        """Ativa/desativa a extensão selecionada"""
        current_item = self.ext_list.currentItem()
        if current_item:
            ext_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.manager.toggle_extension(ext_id)
            self.update_extension_list()

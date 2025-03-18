import json
import os
import shutil
from datetime import datetime
import hashlib
import zipfile
from pathlib import Path

class SyncManager:
    def __init__(self, browser):
        self.browser = browser
        self.sync_dir = Path(os.path.expanduser("~/Documents/NavegadorSync"))
        self.backup_dir = self.sync_dir / "backups"
        self.last_sync = None
        
        # Criar diretórios necessários
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def sync_all_data(self):
        """Sincroniza todos os dados do navegador"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Criar backup dos dados atuais
            backup_path = self.backup_dir / f"backup_{timestamp}.zip"
            self._create_backup(backup_path)
            
            # Dados para sincronizar
            data = {
                'bookmarks': self.browser.bookmarks,
                'history': self.browser.history_manager.get_all(),
                'settings': self.browser.settings.get_all(),
                'timestamp': timestamp
            }
            
            # Salvar dados sincronizados
            for name, content in data.items():
                file_path = self.sync_dir / f"{name}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            
            # Limpar backups antigos (manter últimos 5)
            self._cleanup_old_backups()
            
            self.last_sync = datetime.now()
            self.browser.status_bar.showMessage(
                f"Sincronização local concluída: {self.last_sync.strftime('%H:%M:%S')}")
            
            # Calcular e salvar hash dos arquivos
            self._save_file_hashes()
            
        except Exception as e:
            self.browser.status_bar.showMessage(
                f"Erro na sincronização local: {str(e)}")
    
    def _create_backup(self, backup_path):
        """Cria um backup zipado dos dados"""
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in self.sync_dir.glob('*.json'):
                if file.is_file():
                    zipf.write(file, file.name)
    
    def _cleanup_old_backups(self, keep=5):
        """Mantém apenas os últimos N backups"""
        backups = sorted(self.backup_dir.glob('backup_*.zip'))
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                old_backup.unlink()
    
    def _save_file_hashes(self):
        """Salva hashes dos arquivos sincronizados"""
        hashes = {}
        for file in self.sync_dir.glob('*.json'):
            if file.is_file():
                with open(file, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                hashes[file.name] = file_hash
        
        hash_file = self.sync_dir / 'file_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(hashes, f, indent=2)
    
    def verify_integrity(self):
        """Verifica a integridade dos arquivos sincronizados"""
        hash_file = self.sync_dir / 'file_hashes.json'
        if not hash_file.exists():
            return False
        
        with open(hash_file) as f:
            saved_hashes = json.load(f)
        
        for file_name, saved_hash in saved_hashes.items():
            file_path = self.sync_dir / file_name
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != saved_hash:
                    return False
        return True
    
    def restore_from_backup(self, backup_date=None):
        """Restaura dados de um backup específico ou do mais recente"""
        backups = sorted(self.backup_dir.glob('backup_*.zip'))
        if not backups:
            raise Exception("Nenhum backup encontrado")
        
        # Se não especificado, usa o backup mais recente
        backup_file = backups[-1]
        if backup_date:
            # Procura backup específico
            for b in backups:
                if backup_date in b.name:
                    backup_file = b
                    break
        
        # Criar diretório temporário para restauração
        temp_dir = self.sync_dir / "temp_restore"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Extrair backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Carregar e aplicar dados
            for file in temp_dir.glob('*.json'):
                with open(file, encoding='utf-8') as f:
                    data = json.load(f)
                    if 'bookmarks' in file.name:
                        self.browser.bookmarks = data
                        self.browser.save_bookmarks()
                    elif 'history' in file.name:
                        self.browser.history_manager.restore(data)
                    elif 'settings' in file.name:
                        self.browser.settings.update(data)
            
            self.browser.status_bar.showMessage(
                f"Restauração concluída do backup: {backup_file.name}")
            
        finally:
            # Limpar diretório temporário
            shutil.rmtree(temp_dir, ignore_errors=True)

import subprocess
import sys
import os
import platform

def install_packages():
    print("Instalando dependências para o navegador...")
    
    # Verifica a versão do Python
    python_version = sys.version_info
    print(f"Versão do Python detectada: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Verifica se PIP está disponível e atualizado
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        print(f"Erro ao atualizar pip: {e}")
    
    # Para Python 3.13, precisamos de versões específicas e compatíveis
    if python_version.major == 3 and python_version.minor >= 11:
        print("Detectado Python 3.11 ou superior - usando versões específicas compatíveis")
        packages = [
            "PyQt6==6.6.1",  # Última versão estável
            "PyQt6-Qt6==6.6.1",
            "PyQt6-WebEngine==6.6.0",
            "PyQt6-WebEngine-Qt6==6.6.1"
        ]
    else:
        print("Usando versões padrão para Python 3.7-3.10")
        packages = [
            "PyQt6==6.5.3",
            "PyQt6-Qt6==6.5.3",
            "PyQt6-WebEngine==6.5.0"
        ]
    
    # Instala cada pacote individualmente para melhor controle de erros
    for package in packages:
        try:
            print(f"Instalando {package}...")
            # Força reinstalação para garantir consistência
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", package])
            print(f"Instalação de {package} concluída com sucesso.")
        except Exception as e:
            print(f"Erro ao instalar {package}: {e}")
            print("Tentando uma abordagem alternativa...")
            try:
                # Tenta com --only-binary
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary", ":all:", 
                                      "--upgrade", "--force-reinstall", package])
                print(f"Instalação alternativa de {package} concluída com sucesso.")
            except Exception as e2:
                print(f"Falha na instalação alternativa: {e2}")
                print("Por favor, instale este pacote manualmente.")
    
    # Verificar instalação de WebEngine
    try:
        print("\nVerificando a instalação do PyQt6-WebEngine...")
        check_code = """
import sys
from PyQt6.QtWidgets import QApplication
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    print("PyQt6-WebEngine carregado com sucesso!")
except ImportError as e:
    print(f"Erro ao importar WebEngine: {e}")
    sys.exit(1)
app = QApplication([])
view = QWebEngineView()
print("QWebEngineView criado com sucesso!")
sys.exit(0)
"""
        with open("check_webengine.py", "w") as f:
            f.write(check_code)
        
        result = subprocess.run([sys.executable, "check_webengine.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Verificação concluída com sucesso!")
            print("\n✅ Todas as dependências foram instaladas corretamente!")
            print("   Seu navegador está pronto para uso.")
        else:
            print(f"Erro na verificação: {result.stderr}")
            print(f"Saída: {result.stdout}")
            print("\n⚠️ Houve problemas com a instalação do WebEngine.")
            
    except Exception as e:
        print(f"Erro ao verificar instalação: {e}")
    
    # Cria arquivo de favoritos vazio se não existir
    bookmarks_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookmarks.json")
    if not os.path.exists(bookmarks_file):
        try:
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                f.write('[]')
            print("\nArquivo de favoritos inicializado.")
        except Exception as e:
            print(f"Erro ao criar arquivo de favoritos: {e}")
    
    print("\nInstalação concluída. Verifique se houve erros acima.")
    print("\nCaso ainda haja problemas, tente as seguintes alternativas:")
    print("1. Instale o Microsoft Visual C++ Redistributable mais recente")
    print("2. Verifique se tem o WebView2 Runtime instalado (necessário para WebEngine)")

if __name__ == "__main__":
    install_packages()
    print("\nPara executar o navegador, use o comando:")
    print("python simple_browser.py")

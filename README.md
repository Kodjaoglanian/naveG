<<<<<<< HEAD
# naveg-
=======
# Meu Navegador Simples

Um navegador web moderno baseado em Python e PyQt6 com suporte a múltiplas abas e favoritos.

![Captura de tela](screenshot.png)

## Requisitos

- Python 3.6 ou superior
- PyQt6
- PyQt6-WebEngine

## Instalação

### Método 1: Via pip
Instale as dependências necessárias:

```
pip install -r requirements.txt
```

### Método 2: Via script de instalação (recomendado)
Execute o script de instalação que gerencia melhor as dependências:

```
python setup.py
```

## Execução

Execute o navegador com o comando:

```
python simple_browser.py
```

## Funcionalidades

- ✅ Navegação básica na web
- ✅ Múltiplas abas
- ✅ Botões de avançar, voltar e atualizar
- ✅ Barra de endereço
- ✅ Indicador de progresso de carregamento
- ✅ Gerenciamento de favoritos
- ✅ Atalhos de teclado
- ✅ Menu de contexto (clique direito)
- ✅ Supressão de avisos de console para uma experiência mais limpa

## Atalhos de teclado

| Atalho | Função |
|--------|--------|
| Ctrl+T | Nova aba |
| Ctrl+W | Fechar aba atual |
| Ctrl+R | Recarregar página |
| Alt+Home | Página inicial |
| Ctrl+D | Adicionar aos favoritos |
| Alt+Left | Voltar |
| Alt+Right | Avançar |

## Solução de problemas

Se encontrar o erro `DLL load failed while importing QtWebEngineWidgets`:

1. **Instale os pré-requisitos do sistema**:
   - Microsoft Visual C++ Redistributable (versão mais recente)
   - Microsoft Edge WebView2 Runtime

2. **Tente versões específicas**:
   - Execute `python setup.py` que instalará versões compatíveis

3. **Use a versão alternativa**:
   - Execute `python simple_browser_alternative.py` que oferece um fallback para o navegador do sistema

## Próximos passos

- [ ] Histórico de navegação
- [ ] Bloqueador de anúncios
- [ ] Download de arquivos
- [ ] Modo de navegação privada
- [ ] Temas personalizáveis
- [ ] Extensões

## Notas de versão

- **1.0.0**: Versão inicial com suporte a navegação básica
- **1.1.0**: Migração para PyQt6
- **1.2.0**: Adicionado suporte a múltiplas abas e melhorias na interface
- **1.3.0**: Adicionado suporte a favoritos e atalhos de teclado
>>>>>>> 8114ad3 (Atualização do projeto)

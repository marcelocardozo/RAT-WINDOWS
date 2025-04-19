# Sistema de Monitoramento Remoto

## Visão Geral

O Sistema de Monitoramento Remoto é uma aplicação cliente-servidor desenvolvida em Python para monitoramento de sistemas remotos, oferecendo recursos avançados de gerenciamento e visualização de informações de sistemas. A solução permite administrar e monitorar diversos aspectos de máquinas remotas, incluindo processos, webcam, sistema de arquivos e execução de comandos, tudo através de uma interface gráfica intuitiva.

## Demonstação

[![RAT-WINDOWS](https://img.youtube.com/vi/X9GPy-aV_wI/0.jpg)](https://www.youtube.com/watch?v=X9GPy-aV_wI)


## Características Principais

- 🖥️ Monitoramento remoto de sistemas
- 📊 Coleta de informações do sistema em tempo real
- 📸 Captura e streaming de tela remota
- 📹 Visualização e streaming de webcam
- 📋 Gerenciamento de processos
- 📁 Gerenciamento de arquivos remotos
- 💻 Shell remota
- 🔒 Comunicação segura via socket
- 🛠️ Construtor de Cliente para Geração de Executáveis
- 📝 Histórico de atividades e métricas de sistema
- 🔑 Editor de Registro Windows remoto

## Arquitetura

### Componentes

1. **Servidor**
   - Interface gráfica de gerenciamento baseada em Tkinter
   - Processamento de conexões de clientes com modelo multithread
   - Visualização e análise de informações em tempo real
   - Sistema de gerenciamento de janelas para diferentes funcionalidades
   - Tratamento de erros e resiliência a desconexões

2. **Cliente**
   - Coleta de informações do sistema em background
   - Envio de dados para o servidor via socket
   - Suporte a múltiplas plataformas (Windows, Linux, macOS)
   - Inicialização sob demanda de recursos (webcam, capturas de tela, etc.)
   - Reconexão automática em caso de perda de conexão

### Tecnologias Utilizadas

- **Linguagem**: Python 3.8+
- **Interface Gráfica**: Tkinter
- **Bibliotecas Principais**:
  - `psutil`: Informações do sistema e processos
  - `Pillow`: Manipulação e processamento de imagens
  - `OpenCV`: Acesso à webcam e processamento de vídeo
  - `socket`: Comunicação de rede cliente-servidor
  - `threading`: Suporte a operações paralelas
  - `json`: Serialização e deserialização de dados
  - `PyInstaller`: Geração de executáveis multiplataforma

## Funcionalidades

### Monitoramento do Sistema

- Coleta de informações:
  - Nome do host e usuário atual
  - Sistema operacional e versão
  - Versão do Python e bibliotecas
  - Arquitetura do processador
  - Contagem de CPUs (físicas e lógicas)
  - Memória RAM total e disponível
  - Endereço IP e informações de rede
  - Uso de CPU e RAM em tempo real
  - Informações de disco e armazenamento
  - Tempo de inicialização do sistema

### Histórico de Métricas e Atividades

- **Registro automático de métricas**:
  - Armazenamento de dados históricos de uso de CPU e RAM
  - Registro de picos de utilização de recursos
  - Tendências de uso ao longo do tempo
  - Detecção de anomalias baseada em padrões históricos

- **Histórico de atividades**:
  - Registro de comandos executados via shell remota
  - Histórico de operações de arquivo (uploads, downloads, modificações)
  - Log de conexões e reconexões de clientes
  - Registro de capturas de tela e sessões de webcam
  - Timeline de atividades para análise forense

- **Visualização e análise**:
  - Gráficos de tendência para utilização de recursos
  - Exportação de dados históricos para análise externa
  - Filtragem por períodos e tipos de atividade
  - Alertas baseados em comportamentos anômalos

### Captura e Streaming de Tela

- **Captura única**:
  - Captura em tempo real da tela do cliente
  - Redimensionamento automático para otimização
  - Compressão inteligente para economizar largura de banda
  - Salvamento de imagens em diversos formatos (JPEG, PNG)
  - Visualização com zoom e navegação
  - Atualização automática ou manual

- **Streaming contínuo**:
  - Monitoramento contínuo da tela remota
  - Buffer de frames para renderização suave
  - Ajuste de intervalo de atualização
  - Configuração de qualidade para otimizar performance
  - Controle de taxa de frames para reduzir consumo de rede
  - Opção de atualização sob demanda ou automática
  - Suporte para múltiplos monitores/telas
  - Visualização em tempo real das atividades do usuário remoto

### Webcam

- Listagem de todas as câmeras disponíveis no sistema
- Detecção automática de resolução e capacidades
- Captura única de frames com qualidade ajustável
- Streaming contínuo em tempo real com buffer otimizado
- Ajuste de qualidade de imagem via interface gráfica
- Salvamento de capturas com timestamp
- Inicialização sob demanda (só ativa quando solicitado)
- Exibição de métricas de FPS (frames por segundo)
- Gerenciamento inteligente de recursos da câmera
- Tratamento de erros e reconexão automática

### Gerenciamento de Processos

- Lista completa de processos em execução
- Filtragem e pesquisa de processos por nome
- Atualização automática em intervalos configuráveis
- Opção para exibir ou ocultar processos parados
- Informações detalhadas:
  - PID (Process ID)
  - Nome do processo e caminho executável
  - Usuário proprietário
  - Uso de CPU e tendência
  - Uso de memória (absoluto e percentual)
  - Tempo de execução
  - Contador de threads
  - Argumentos de linha de comando
- Encerramento remoto de processos (normal ou forçado)
- Visualização hierárquica (processos pai/filho)

### Gerenciamento de Arquivos

- Navegação completa pelo sistema de arquivos remoto
- Visualização em estilo explorador de arquivos
- Upload e download de arquivos com progresso
- Suporte a arquivos de qualquer tamanho (transferência em chunks)
- Criação, renomeação e exclusão de arquivos/pastas
- Visualização de propriedades detalhadas:
  - Tamanho
  - Data de modificação
  - Permissões
  - Tipo de arquivo
- Operações de cópia e movimentação
- Verificação de integridade de transferências

### Editor de Registro do Windows

- Acesso completo e navegação pelo Registro do Windows remoto
- Suporte para todas as principais hives do registro:
  - HKEY_CLASSES_ROOT
  - HKEY_CURRENT_USER
  - HKEY_LOCAL_MACHINE
  - HKEY_USERS
  - HKEY_CURRENT_CONFIG
- Visualização hierárquica em árvore das chaves do registro
- Exibição detalhada de valores com tipos e dados
- Operações completas de edição:
  - Criação de novas chaves e valores
  - Edição de valores existentes com validação por tipo
  - Exclusão de chaves e valores
  - Renomeação de entradas
- Suporte para todos os tipos de dados do registro:
  - REG_SZ (String)
  - REG_DWORD (Valor de 32 bits)
  - REG_BINARY (Dados binários)
  - REG_MULTI_SZ (Múltiplas strings)
  - REG_EXPAND_SZ (String expansível)
- Interface visual intuitiva:
  - Navegação por caminho direto
  - Visualização em painéis divididos (chaves e valores)
  - Menus de contexto para operações comuns
  - Feedback em tempo real das operações
- Tratamento robusto de erros e permissões
- Validação de dados por tipo para evitar corrupção do registro
- Confirmação para operações potencialmente perigosas
- Atualização automática após modificações
- Histórico de navegação para fácil retorno a chaves visitadas anteriormente

### Shell Remota

- Execução de comandos remotos em tempo real
- Visualização colorizada da saída de comandos
- Distinção entre saída padrão e erros
- Histórico de comandos com navegação
- Suporte a diferentes sistemas operacionais
- Terminação segura de comandos
- Ambiente de execução configurável

### Construtor de Cliente

- Ferramenta gráfica para criação de executáveis personalizados
- Geração simplificada de clientes para diferentes ambientes
- Configuração flexível de parâmetros de conexão
- Suporte para múltiplas plataformas (Windows, Linux, macOS)

#### Recursos do Construtor

- Configuração de host e porta do servidor
- Personalização do nome do processo cliente
- Geração de executável único ou em diretório
- Opção de ocultar console durante execução
- Suporte para ícone personalizado
- Log detalhado do processo de compilação
- Detecção automática de dependências

#### Modos de Geração

- **Arquivo Único**:
  - Compila todo o cliente em um único executável
  - Ideal para distribuição simplificada
  - Maior tempo de inicialização inicial

- **Diretório**:
  - Gera pasta com executável e dependências
  - Inicialização mais rápida
  - Maior flexibilidade para modificações

#### Exemplo de Configuração

```python
# Configurações padrão do construtor
DEFAULT_SERVER_HOST = "10.100.3.203"
DEFAULT_SERVER_PORT = 5000
```

#### Casos de Uso

- Distribuição rápida de cliente de monitoramento
- Implantação em ambientes corporativos
- Criação de pacotes para diferentes sistemas operacionais
- Personalização de configurações de conexão

## Protocolo de Comunicação

### Arquitetura do Protocolo

O sistema utiliza um protocolo binário proprietário baseado em comandos identificados por códigos numéricos. Cada mensagem contém um cabeçalho com o código de comando seguido opcionalmente por um campo de tamanho e os dados associados.

### Formato de Mensagem

```
[Código de Comando - 4 bytes] [Tamanho dos Dados - 4 bytes (opcional)] [Dados]
```

### Comandos Principais

- **Sistema e Conectividade**
  - `CMD_UPDATE` (1): Atualização de informações do sistema
  - `CMD_PING` (2): Verificação de conectividade (cliente → servidor)
  - `CMD_PONG` (3): Resposta de verificação (servidor → cliente)

- **Captura de Tela**
  - `CMD_SCREENSHOT_SINGLE` (4): Solicitação de captura única
  - `CMD_SCREENSHOT_RESPONSE` (5): Resposta com dados da captura
  - `CMD_SCREENSHOT_STREAM_START` (6): Iniciar streaming contínuo da tela
  - `CMD_SCREENSHOT_STREAM_STOP` (7): Parar streaming da tela

- **Gerenciamento de Processos**
  - `CMD_PROCESS_LIST` (10): Solicitação de lista de processos
  - `CMD_PROCESS_LIST_RESPONSE` (11): Resposta com lista de processos
  - `CMD_PROCESS_KILL` (12): Solicitação de encerramento de processo
  - `CMD_PROCESS_KILL_RESPONSE` (13): Resposta do encerramento

- **Shell Remota**
  - `CMD_SHELL_COMMAND` (20): Envio de comando para execução
  - `CMD_SHELL_RESPONSE` (21): Resposta com saída do comando

- **Gerenciamento de Arquivos**
  - `CMD_FILE_LIST` (30): Solicitação de listagem de arquivos
  - `CMD_FILE_LIST_RESPONSE` (31): Resposta com lista de arquivos
  - `CMD_FILE_DOWNLOAD` (32): Solicitação de download de arquivo
  - `CMD_FILE_DOWNLOAD_RESPONSE` (33): Resposta com conteúdo do arquivo
  - `CMD_FILE_UPLOAD` (34): Envio de arquivo para cliente
  - `CMD_FILE_UPLOAD_RESPONSE` (35): Confirmação de recebimento
  - `CMD_FILE_DELETE` (36): Solicitação de exclusão de arquivo
  - `CMD_FILE_DELETE_RESPONSE` (37): Confirmação de exclusão
  - `CMD_FILE_RENAME` (38): Solicitação de renomeação
  - `CMD_FILE_RENAME_RESPONSE` (39): Confirmação de renomeação
  - `CMD_FILE_MKDIR` (40): Solicitação de criação de diretório
  - `CMD_FILE_MKDIR_RESPONSE` (41): Confirmação de criação

- **Webcam**
  - `CMD_WEBCAM_LIST` (50): Solicitação de lista de câmeras
  - `CMD_WEBCAM_LIST_RESPONSE` (51): Resposta com câmeras disponíveis
  - `CMD_WEBCAM_CAPTURE` (52): Solicitação de captura única
  - `CMD_WEBCAM_CAPTURE_RESPONSE` (53): Resposta com frame capturado
  - `CMD_WEBCAM_STREAM_START` (54): Iniciar streaming contínuo
  - `CMD_WEBCAM_STREAM_STOP` (55): Parar streaming

- **Editor de Registro**
  - `CMD_REGISTRY_LIST` (80): Solicitação de listagem de chaves
  - `CMD_REGISTRY_LIST_RESPONSE` (81): Resposta com chaves e valores
  - `CMD_REGISTRY_READ` (82): Solicitação de leitura de valor
  - `CMD_REGISTRY_READ_RESPONSE` (83): Resposta com dados do valor
  - `CMD_REGISTRY_WRITE` (84): Solicitação de escrita de valor
  - `CMD_REGISTRY_WRITE_RESPONSE` (85): Confirmação de escrita
  - `CMD_REGISTRY_DELETE_VALUE` (86): Solicitação de exclusão de valor
  - `CMD_REGISTRY_DELETE_VALUE_RESPONSE` (87): Confirmação de exclusão
  - `CMD_REGISTRY_CREATE_KEY` (88): Solicitação de criação de chave
  - `CMD_REGISTRY_CREATE_KEY_RESPONSE` (89): Confirmação de criação
  - `CMD_REGISTRY_DELETE_KEY` (90): Solicitação de exclusão de chave
  - `CMD_REGISTRY_DELETE_KEY_RESPONSE` (91): Confirmação de exclusão

- **Histórico**
  - `CMD_HISTORY_GET` (70): Solicitar dados históricos
  - `CMD_HISTORY_RESPONSE` (71): Resposta com dados históricos
  - `CMD_HISTORY_RECORD` (72): Registrar evento no histórico
  - `CMD_HISTORY_CLEAR` (73): Limpar dados históricos

- **Códigos de Status**
  - `STATUS_OK` (100): Operação bem-sucedida
  - `STATUS_ERROR` (200): Erro genérico
  - `STATUS_TIMEOUT` (201): Timeout na operação
  - `STATUS_CONNECTION_ERROR` (202): Erro de conexão
  - `STATUS_ACCESS_DENIED` (203): Acesso negado
  - `STATUS_NOT_FOUND` (204): Recurso não encontrado

## Requisitos de Instalação

### Requisitos de Sistema

- Python 3.8 ou superior
- Pelo menos 100MB de RAM disponível
- Conexão de rede entre cliente e servidor
- Privilégios suficientes para monitoramento de sistema

### Dependências

```
pip install psutil pillow opencv-python PyInstaller
```

### Instalação Manual

1. Clone o repositório
2. Instale as dependências
3. Configure os parâmetros em `config.py`
4. Execute o servidor e os clientes

## Configuração

### Configurações do Servidor (`server/config.py`)

```python
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
BUFFER_SIZE = 8192
SOCKET_TIMEOUT = 5.0
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
SCREENSHOT_QUALITY = 75
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
UPDATE_INTERVAL = 0.5  # segundos
AUTO_REFRESH_INTERVAL = 3  # segundos
DEBOUNCE_DELAY = 100  # milissegundos
LOG_DIR = "logs"
MAX_CLIENTS = 50
MAX_PROCESSES_PER_CLIENT = 500
MAX_SCREENSHOT_SIZE = 20 * 1024 * 1024  # 20MB
SCREEN_STREAM_INTERVAL = 0.2  # Intervalo entre frames da tela em segundos
HISTORY_RETENTION_DAYS = 30  # Período de retenção do histórico em dias
HISTORY_SAMPLE_INTERVAL = 60  # Intervalo em segundos para amostragem de métricas no histórico
```

### Configurações do Cliente (`client/config.py`)

```python
DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 5000
RECONNECT_DELAY_INITIAL = 5
RECONNECT_DELAY_MAX = 30
SOCKET_TIMEOUT = 5.0
CONNECTION_RETRY_COUNT = 3
SCREENSHOT_MAX_SIZE = 1024
SCREENSHOT_QUALITY = 75
SCREENSHOT_FORMAT = "JPEG"
UPDATE_INTERVAL = 0.5
PING_INTERVAL = 3.0
PROCESS_SCAN_INTERVAL = 2.0
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = "client.log"
LOG_DIR = "logs"
MAX_LOG_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 3
BUFFER_SIZE = 8192
MAX_IMAGE_SIZE = 10 * 1024 * 1024
WEBCAM_MAX_SIZE = 640  # Tamanho máximo (largura/altura) para redimensionamento
WEBCAM_QUALITY = 50    # Qualidade JPEG (0-100)
WEBCAM_FORMAT = "JPEG" # Formato da imagem (JPEG, PNG)
WEBCAM_STREAM_INTERVAL = 0.1  # Intervalo entre frames em segundos
SCREEN_STREAM_INTERVAL = 0.2  # Intervalo entre frames da tela em segundos
SCREEN_STREAM_QUALITY = 50    # Qualidade de compressão para streaming de tela
HISTORY_ENABLED = True  # Habilita o registro local de histórico de métricas
HISTORY_LOCAL_PATH = "history"  # Diretório para armazenamento local do histórico
```

## Execução

### Iniciando o Servidor

```bash
python server/main.py
```

Opções adicionais:
- `--host HOST`: Define o endereço de escuta (padrão: 0.0.0.0)
- `--port PORT`: Define a porta de escuta (padrão: 5000)
- `--log-level LEVEL`: Define o nível de log (DEBUG, INFO, WARNING, ERROR)

### Iniciando o Cliente

```bash
python client/main.py [--host HOST] [--port PORT]
```

Opções adicionais:
- `--host HOST`: Define o endereço do servidor (padrão: 127.0.0.1)
- `--port PORT`: Define a porta do servidor (padrão: 5000)
- `--no-reconnect`: Desativa a reconexão automática
- `--log-level LEVEL`: Define o nível de log (DEBUG, INFO, WARNING, ERROR)

## Segurança

- Comunicação via socket com validação de comandos
- Sanitização de entradas e parâmetros
- Proteção contra comandos maliciosos ou inválidos
- Limitação de acesso a recursos críticos do sistema
- Inicialização de recursos sob demanda (webcam, etc.)
- Validação de tipo e tamanho de dados
- Tratamento de erros para evitar vazamento de informações

## Otimizações e Melhorias

### Performance

- **Streaming de Tela**:
  - Compressão adaptativa baseada em mudanças na tela
  - Detecção de áreas de mudança para transmissão parcial
  - Suporte para diferentes resoluções e taxas de quadros
  - Otimização para baixa largura de banda
  - Buffer de frames com prioridade para renderização

- **Streaming de Webcam**:
  - Buffer de frames para renderização suave
  - Manutenção de conexão aberta com a câmera
  - Processamento assíncrono de frames
  - Compressão e redimensionamento otimizados

- **Gerenciamento de Memória**:
  - Liberação de recursos não utilizados
  - Controle de tamanho de buffer
  - Transferência de arquivos grandes em chunks
  - Limpeza automática de objetos temporários

- **Rede**:
  - Compressão de dados para economizar banda
  - Reconexão automática com backoff exponencial
  - Verificação periódica de conectividade (ping/pong)
  - Timeout adaptativo para operações

- **Histórico**:
  - Amostragem adaptativa baseada em mudanças significativas
  - Compressão de séries temporais para armazenamento eficiente
  - Agregação de dados históricos para minimizar armazenamento
  - Limpeza automática de dados antigos conforme políticas de retenção

### Interface do Usuário

- **Streaming de Tela**:
  - Controle de taxa de atualização (FPS)
  - Ajuste de qualidade de imagem
  - Opções de escala (ajustar à janela, tamanho real)
  - Seleção de monitor em sistemas multi-monitor
  - Indicadores de performance da rede

- **Webcam**:
  - Controle deslizante de qualidade (10% a 90%)
  - Exibição em tempo real de FPS
  - Seleção de câmera com visualização de resolução
  - Status detalhado de operações

- **Gerenciamento de Janelas**:
  - Interface multi-janela para diferentes funcionalidades
  - Posicionamento inteligente na tela
  - Redimensionamento responsivo
  - Centralização automática

- **Feedback Visual**:
  - Indicadores de progresso para operações longas
  - Mensagens de status detalhadas
  - Tratamento visual de erros
  - Confirmação de ações críticas

- **Visualização de Histórico**:
  - Painéis de controle com gráficos de tendência
  - Visualização de linha do tempo de eventos
  - Filtros interativos por período e tipo de evento
  - Exportação de relatórios e dados históricos

## Componentes Detalhados

### Cliente (`client/`)

#### Coletores (`collectors/`)

1. **`process_collector.py`**
   - Coleta e filtra processos do sistema
   - Obtém informações detalhadas de cada processo
   - Suporta diferentes níveis de detalhamento
   - Monitora uso de recursos por processo

2. **`screenshot_collector.py`**
   - Captura telas usando APIs do sistema
   - Processa e otimiza imagens capturadas
   - Suporta múltiplos monitores
   - Gerencia configurações de qualidade e formato
   - Implementa captura contínua para streaming
   - Otimiza detecção e transmissão de mudanças na tela

3. **`system_collector.py`**
   - Coleta informações gerais do sistema
   - Monitora recursos de hardware
   - Agrega dados de rede, CPU, memória e disco
   - Formata dados para transmissão eficiente

4. **`webcam_collector.py`**
   - Gerencia acesso às câmeras do sistema
   - Escaneia dispositivos disponíveis sob demanda
   - Mantém pool de conexões ativas para melhor performance
   - Captura e otimiza frames de acordo com parâmetros
   - Monitoramento de estado das câmeras
   - Recuperação automática de erros de captura
   - Liberação segura de recursos

5. **`history_collector.py`**
   - Coleta e armazena métricas históricas do sistema
   - Implementa políticas de amostragem e agregação
   - Gerencia armazenamento local de dados históricos
   - Sincroniza histórico com servidor quando solicitado

#### Core (`core/`)

1. **`client_connector.py`**
   - Estabelece e mantém conexão com o servidor
   - Implementa reconexão automática com backoff
   - Gerencia estados de conexão
   - Roteia mensagens para handlers apropriados

2. **`command_handler.py`**
   - Processa comandos recebidos do servidor
   - Distribui comandos para os gerenciadores adequados
   - Implementa protocolo de comunicação
   - Valida entradas e saídas de dados
   - Gerencia streaming de webcam
   - Gerencia streaming de webcam e tela
   - Manipula operações de arquivo

3. **`data_sender.py`**
   - Envia atualizações periódicas para o servidor
   - Implementa batching de mensagens
   - Gerencia prioridade de mensagens
   - Controla fluxo de dados (throttling)

4. **`protocol.py`**
   - Define constantes e valores do protocolo
   - Mantém códigos de comando
   - Define estruturas de mensagens
   - Implementa códigos de status

#### Managers (`managers/`)

1. **`client_manager.py`**
   - Coordena todos os outros gerenciadores
   - Inicializa e encerra componentes
   - Gerencia ciclo de vida do cliente
   - Controla estados globais

2. **`file_manager.py`**
   - Gerencia operações de arquivo
   - Implementa operações de diretório
   - Controla transferências de arquivos
   - Processa solicitações de manipulação de arquivos

3. **`process_manager.py`**
   - Gerencia lista de processos em execução
   - Controla operações de processos
   - Implementa encerramento de processos
   - Monitora processos críticos

4. **`screenshot_manager.py`**
   - Coordena capturas de tela
   - Gerencia configurações de captura
   - Controla intervalo e qualidade
   - Processa solicitações de captura
   - Implementa modo de streaming contínuo
   - Gerencia threads de streaming da tela
   - Otimiza estratégias de compressão

5. **`system_manager.py`**
   - Gerencia dados do sistema
   - Coleta informações periódicas
   - Mantém estatísticas de uso
   - Implementa detecção de mudanças

6. **`webcam_manager.py`**
   - Interface de alto nível para funcionalidades de webcam
   - Inicialização sob demanda do coletor
   - Coordenação de streaming contínuo
   - Gerenciamento de qualidade e intervalos
   - Tratamento de erros e recuperação
   - Controle de recursos de câmera
   - Callback para envio de frames capturados
   - Gerenciamento de threads de streaming

7. **`history_manager.py`**
   - Interface para gerenciamento de histórico
   - Coordena coleta periódica de métricas
   - Implementa armazenamento e recuperação de histórico
   - Gerencia sincronização com o servidor
   - Implementa políticas de retenção de dados
   - Fornece APIs para consulta e análise de histórico

8. **`registry_manager.py`**
   - Interface para gerenciamento do registro do Windows
   - Acesso controlado às hives do registro através do WinReg
   - Listagem hierárquica de chaves e valores
   - Operações CRUD (Criar, Ler, Atualizar, Deletar) para chaves e valores
   - Validação de tipo e formato de dados
   - Tratamento seguro de permissões e erros
   - Mapeamento entre tipos internos do registro e representações amigáveis
   - Sanitização e validação de entradas para prevenir danos ao registro

#### Utils (`utils/`)

1. **`image_utils.py`**
   - Funções para processamento de imagens
   - Redimensionamento e compressão
   - Conversão entre formatos
   - Validação de imagens
   - Otimização para streaming
   - Comparação de imagens para detecção de mudanças

2. **`logger.py`**
   - Configuração de logging centralizada
   - Rotação e backup de logs
   - Formatação de mensagens
   - Controle de níveis de log

3. **`network_utils.py`**
   - Funções auxiliares para rede
   - Obtenção de endereço IP
   - Teste de conectividade
   - Operações de socket

4. **`process_utils.py`**
   - Funções para manipulação de processos
   - Utilitários para encerramento
   - Formatação de informações
   - Detecção de relações entre processos

5. **`system_utils.py`**
   - Funções para informações do sistema
   - Detecção de plataforma
   - Obtenção de hardware
   - Formatação de estatísticas

6. **`history_utils.py`**
   - Funções para agregação de dados históricos
   - Algoritmos de compressão de séries temporais
   - Detecção de outliers e anomalias
   - Exportação e importação de dados históricos
   - Visualização de dados temporais

### Servidor (`server/`)

#### Core (`core/`)

1. **`client_manager.py`**
   - Gerencia clientes conectados
   - Mantém registro de sessões
   - Rastreia estados dos clientes
   - Coordena atualizações de UI

2. **`command_processor.py`**
   - Processa comandos recebidos dos clientes
   - Encaminha para handlers apropriados
   - Valida dados recebidos
   - Formata respostas

3. **`connection_manager.py`**
   - Gerencia conexões de socket
   - Aceita novas conexões
   - Distribui para handlers
   - Monitora estados de conexão

4. **`protocol.py`**
   - Define constantes do protocolo
   - Implementa códigos de comando
   - Define estruturas de mensagens
   - Mantém códigos de status

5. **`socket_server.py`**
   - Implementa servidor multithreaded
   - Escuta por conexões
   - Gerencia ciclo de vida do servidor
   - Coordena outros componentes

#### GUI (`gui/`)

1. **`client_view.py`**
   - Visualização de clientes conectados
   - Exibe informações básicas
   - Permite seleção para ações
   - Atualização automática de status

2. **`file_manager_view.py`**
   - Interface de gerenciamento de arquivos
   - Navegação em árvore de diretórios
   - Operações de arquivo
   - Visualização de propriedades

3. **`log_view.py`**
   - Visualização de logs em tempo real
   - Filtro e pesquisa
   - Auto-scroll configurável
   - Exportação de logs

4. **`main_window.py`**
   - Janela principal do aplicativo
   - Coordena outros componentes visuais
   - Gerencia menu e ações
   - Controla estado global da UI

5. **`process_list.py`**
   - Componente de lista de processos
   - Visualização em formato de tabela
   - Ordenação e filtro
   - Ações contextuais

6. **`process_view.py`**
   - Visualização detalhada de processos
   - Gráficos de uso
   - Controles de processos
   - Informações estendidas

7. **`screenshot_view.py`**
   - Visualização de capturas de tela
   - Zoom e navegação
   - Salvamento e exportação
   - Atualização automática/manual
   - Exibição de streaming contínuo de tela
   - Controles de FPS e qualidade
   - Indicadores de performance

8. **`shell_view.py`**
   - Interface de terminal remoto
   - Entrada de comandos
   - Visualização de saída
   - Histórico de comandos

9. **`styles.py`**
   - Definição de estilos de UI
   - Temas e cores
   - Fontes e tamanhos
   - Elementos visuais comuns

10. **`webcam_view.py`**
    - Interface de visualização de webcam
    - Controles de câmera e streaming
    - Ajuste de qualidade via slider
    - Exibição de FPS e estatísticas
    - Buffer para exibição suave
    - Salvamento de capturas
    - Gerenciamento otimizado de recursos de imagem
    - Renderização eficiente de frames
    - Tratamento de redimensionamento

11. **`window_manager.py`**
    - Gerenciamento de múltiplas janelas
    - Posicionamento inteligente
    - Coordenação de atualizações
    - Gerenciamento de recursos visuais

12. **`registry_view.py`**
    - Interface completa para o editor de registro
    - Visualização em árvore de chaves e valores
    - Navegação por caminho direto
    - Visualização em painel dividido (chaves e valores)
    - Menus de contexto para operações
    - Formulários de edição tipados para valores
    - Validação de entrada por tipo de dado
    - Confirmação para operações críticas
    - Atualizações em tempo real após modificações
    - Tratamento visual de erros e permissões
    - Histórico de navegação e breadcrumbs

13. **`history_view.py`**
    - Visualização de dados históricos
    - Gráficos de tendência interativos
    - Filtros por período e métricas
    - Exportação de dados e relatórios
    - Detecção e destaque de anomalias
    - Comparação de períodos históricos

#### Handlers (`handlers/`)

1. **`client_handler.py`**
   - Manipula conexões de clientes
   - Processa comunicação individual
   - Gerencia estado do cliente
   - Implementa protocolo

2. **`process_handler.py`**
   - Manipula operações de processos
   - Processa solicitações de lista
   - Implementa encerramento
   - Formata resultados

3. **`screenshot_handler.py`**
   - Manipula capturas de tela
   - Processa imagens recebidas
   - Otimiza para visualização
   - Entrega para componentes de UI
   - Processa streaming contínuo de tela
   - Gerencia configurações de qualidade e FPS

4. **`history_handler.py`**
   - Processa solicitações de dados históricos
   - Gerencia sincronização de histórico entre cliente e servidor
   - Implementa consultas e filtragem de dados históricos
   - Coordena agregação de dados para visualização

#### Managers (`managers/`)

1. **`log_manager.py`**
   - Gerencia logs do servidor
   - Configura formatos e destinos
   - Rotaciona arquivos de log
   - Distribui mensagens

2. **`monitoring_manager.py`**
   - Gerencia dados de monitoramento
   - Mantém histórico de métricas
   - Calcula estatísticas
   - Detecta anomalias

3. **`process_manager.py`**
   - Gerencia dados de processos
   - Processa listas recebidas
   - Mantém histórico de processos
   - Formata para visualização

4. **`history_manager.py`**
   - Armazena dados históricos de todos os clientes
   - Implementa banco de dados de séries temporais
   - Fornece APIs para consulta e análise
   - Gerencia políticas de retenção
   - Implementa alertas baseados em padrões históricos
   - Coordena exportação de relatórios

#### Utils (`utils/`)

1. **`image_utils.py`**
   - Funções para processamento de imagens
   - Decodificação e otimização
   - Redimensionamento e compressão
   - Validação e conversão

2. **`network_utils.py`**
   - Funções auxiliares para rede
   - Envio e recebimento de dados
   - Operações de socket
   - Validação de conexão

3. **`simple_binary_upload.py`**
   - Implementação de upload binário
   - Processamento de grandes arquivos
   - Validação de integridade
   - Monitoramento de progresso

4. **`threading_utils.py`**
   - Utilitários para threading
   - Pools de threads
   - Sincronização
   - Debouncing e throttling

5. **`ui_utils.py`**
   - Componentes de UI reutilizáveis
   - Diálogos comuns
   - Formatação de elementos
   - Helpers de layout

6. **`history_utils.py`**
   - Funções de análise de séries temporais
   - Algoritmos de detecção de anomalias
   - Renderização de gráficos e visualizações
   - Ferramentas de exportação de dados

## Funcionalidades Avançadas

### Streaming de Tela Otimizado

- **Inicialização sob demanda**:
  - O streaming só é ativado quando explicitamente solicitado
  - Nenhum overhead quando não está em uso
  - Configurações flexíveis por cliente

- **Performance otimizada**:
  - Detecção de áreas modificadas para transmissão seletiva
  - Compressão adaptativa baseada em conteúdo
  - Ajuste dinâmico de qualidade conforme largura de banda
  - Processamento multi-thread para minimizar latência

- **Buffer de frames**:
  - Buffer circular para eliminar jitter
  - Priorização de frames mais recentes
  - Descarte inteligente em caso de sobrecarga

### Streaming de Webcam Otimizado

- **Inicialização sob demanda**:
  - A webcam só é ativada quando explicitamente solicitado
  - Nenhum acesso à câmera durante a inicialização do programa
  - Recursos liberados quando não em uso

- **Conexão persistente**:
  - Mantém a conexão com a webcam aberta durante o streaming
  - Evita o constante ligar/desligar da câmera
  - Reduz latência e melhora a experiência

- **Buffer de frames**:
  - Implementa um buffer circular para frames
  - Renderização suave mesmo com variações de rede
  - Prioriza frames mais recentes

- **Qualidade adaptativa**:
  - Controle deslizante para ajuste de qualidade (10%-90%)
  - Aplicação imediata de alterações
  - Balanceamento entre qualidade e desempenho

- **Métricas em tempo real**:
  - Exibição de FPS (frames por segundo)
  - Estatísticas de tamanho dos frames
  - Monitoramento de saúde da conexão

- **Gerenciamento inteligente de recursos**:
  - Detecção e recuperação de erros
  - Liberação automática de câmeras não utilizadas
  - Limite de erros consecutivos antes de parar

### Editor de Registro Windows Avançado

- **Inicialização sob demanda**:
  - Interface carregada apenas quando solicitada
  - Otimização de recursos e desempenho
  - Carga preguiçosa (lazy loading) de dados

- **Navegação otimizada**:
  - Sistema de busca e filtro para chaves e valores
  - Histórico de navegação com breadcrumbs
  - Favoritos para acesso rápido a chaves frequentes
  - Suporte para copiar/colar caminhos completos

- **Operações em lote**:
  - Importação/exportação de chaves completas
  - Operações recursivas (excluir com subchaves)
  - Confirmação para operações potencialmente perigosas

- **Validação inteligente**:
  - Verificação de tipos de dados por validadores específicos
  - Sugestões de formato para dados binários e hex
  - Prevenção de entradas que poderiam danificar o registro
  - Restauração automática em caso de falha de operação

- **Informações detalhadas**:
  - Visualização de permissões por chave
  - Detecção de valores protegidos pelo sistema
  - Documentação integrada sobre chaves comuns
  - Alertas para modificações em áreas sensíveis

### Gerenciamento de Arquivos Remoto

- **Navegação completa**:
  - Visualização em estilo explorador
  - Histórico de navegação
  - Caminhos favoritos
  - Atualização automática/manual

- **Transferência otimizada**:
  - Upload/download em chunks para arquivos grandes
  - Progresso em tempo real
  - Validação de integridade
  - Retomada de transferências

- **Operações de arquivo**:
  - Criação, renomeação, movimentação, exclusão
  - Operações em lote
  - Confirmação para ações destrutivas
  - Tratamento de erros de permissão

### Sistema de Histórico Avançado

- **Coleta automática de métricas**:
  - Registro periódico de dados de desempenho
  - Amostragem adaptativa baseada em mudanças significativas
  - Histórico de eventos e operações importantes
  - Catalogação de atividades por tipo e severidade

- **Armazenamento eficiente**:
  - Compressão de dados de séries temporais
  - Agregação automática em diferentes resoluções temporais
  - Limpeza programada de dados antigos
  - Sincronização sob demanda entre cliente e servidor

- **Análise e visualização**:
  - Gráficos de tendência com múltiplas métricas
  - Comparação entre períodos diferentes
  - Detecção e alerta de padrões anômalos
  - Exportação para formatos de análise externa

- **Inteligência operacional**:
  - Geração de relatórios de uso
  - Predição de tendências baseada em histórico
  - Alertas proativos de problemas potenciais
  - Insights sobre comportamento dos sistemas monitorados

## Suporte

Em caso de problemas, abra uma issue no repositório do projeto com as seguintes informações:
- Versão do sistema operacional
- Versão do Python
- Logs relevantes
- Passos para reproduzir o problema

## Autores

Marcelo Cardozo

---

**Nota**: Esta documentação está sujeita a alterações. Sempre consulte a
**versão mais recente.
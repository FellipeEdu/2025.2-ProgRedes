import os

# IP servidor
HOST_IP_SERVER  = '192.168.56.1'

# IP cliente
HOST_IP_CLIENT  = ''

# Porta
HOST_PORT       = 20000           

# Tupla do servidor
TUPLA_SERVER    = (HOST_IP_SERVER, HOST_PORT)
TUPLA_CLIENTE   = (HOST_IP_CLIENT, HOST_PORT)

# Codificação de caracteres
CODE_PAGE       = 'utf-8'    

# Tamanho do buffer
BUFFER_SIZE     = 1024

# Timeout do socket em segundos
TIMEOUT_SOCKET  = 1

# Operações (1 byte)
OP_DOWNLOAD = 10
OP_LIST = 20
OP_UPLOAD = 30
OP_RESUME = 40
OP_MASK = 50

# Status (1 byte)
STATUS_OK = 1
STATUS_ERRO = 0
STATUS_NOT_FOUND = 10
STATUS_HASH_INVALIDO = 20

# Diretórios de arquivos de imagens no servidor e cliente
BASE_DIR = os.path.dirname(__file__)
DIR_IMG_SERVER  = os.path.join(BASE_DIR, 'server_files')
DIR_IMG_CLIENT  = os.path.join(BASE_DIR, 'client_files')

# --------------------------------------------------------------------------------
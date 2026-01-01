import os

# IP servidor
HOST_IP_SERVER  = '10.25.1.16'

# IP cliente
HOST_IP_CLIENT  = '10.25.2.214'

# Porta
HOST_PORT       = 50000           

# Tupla do servidor
TUPLA_SERVER    = (HOST_IP_SERVER, HOST_PORT)
TUPLA_CLIENTE   = (HOST_IP_CLIENT, HOST_PORT)

# Codificação de caracteres
CODE_PAGE       = 'utf-8'    

# Tamanho do buffer
BUFFER_SIZE     = 512

# Timeout do socket em segundos
TIMEOUT_SOCKET  = 0.5

# Diretórios de arquivos de imagens no servidor e cliente
DIR_IMG_SERVER  = os.path.dirname(__file__) + '\\server_files'
DIR_IMG_CLIENT  = os.path.dirname(__file__) + '\\client_files'

# --------------------------------------------------------------------------------
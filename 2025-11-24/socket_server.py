import socket

# ----------------------------------------------------------------------
HOST_IP_SERVER  = ''              # Definindo o IP do servidor
HOST_PORT       = 50000           # Definindo a porta

BUFFER_SIZE     = 512             # Tamanho do buffer
CODE_PAGE       = 'utf-8'         # Definindo a página de 
                                  # codificação de caracteres
# ----------------------------------------------------------------------

# Criando o socket (socket.AF_INET -> IPV4 / socket.SOCK_DGRAM -> UDP)
sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Ligando o socket à porta
sockServer.bind( (HOST_IP_SERVER, HOST_PORT) ) 

print('\nRecebendo Mensagens...\n\n')

while True:
    # Recebendo os dados do cliente
    byteMensagem, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)

    # Imprimindo a mensagem recebida convertendo de bytes para string
    print(f'{tuplaCliente}: {byteMensagem.decode(CODE_PAGE)}')
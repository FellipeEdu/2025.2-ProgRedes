# Importando a biblioteca SOCKET
import socket

# ----------------------------------------------------------------------
HOST_IP_SERVER  = ''              # Definindo o IP do servidor
HOST_PORT       = 50000           # Definindo a porta
CODE_PAGE       = 'utf-8'         # Definindo a página de 
                                  # codificação de caracteres
BUFFER_SIZE     = 512             # Tamanho do buffer
# ----------------------------------------------------------------------


# Criando o socket (socket.AF_INET -> IPV4 / socket.SOCK_STREAM -> TCP)
sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Ligando o socket à porta
sockTCP.bind((HOST_IP_SERVER, HOST_PORT)) 

# Tornando o socket capaz de escutar conexões - Tamanho da fila de conexões pendentes
#sockTCP.listen(5)

# definindo tempo de vida
sockTCP.settimeout(0.5)

print('\nRecebendo Mensagens...\n\n')

try:
    while True:
        try:
             # Recebendo os dados do cliente
            byteMensagem, tuplaCliente,  = sockTCP.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            continue
        else:
            strNomeHost = socket.gethostbyaddr(tuplaCliente[0])[0]
            strHost = strNomeHost.split('.')[0].upper()

            # Imprimindo a mensagem recebida convertendo de bytes para string
            print(f'{tuplaCliente} -> {strHost}: {byteMensagem.decode(CODE_PAGE)}')
            
except KeyboardInterrupt:
    print('\nAVISO: foi pressionado CTRL+C.\nSaindo do servidor...\n')
finally:
    # Fechando o socket
    sockTCP.close()
    print('AVISO: Servidor finalizado...')


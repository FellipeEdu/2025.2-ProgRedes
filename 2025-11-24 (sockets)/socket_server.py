#
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

# definindo tempo de vida
sockServer.settimeout(0.5)

print('\nRecebendo Mensagens...\n')
print('Pressione CTRL+C para sair do Servidor.\n')
print(f'MENSAGENS ABAIXO\n{'-' * 50}')

try:
    while True:
        try:
             # Recebendo os dados do cliente
            byteMensagem, tuplaCliente,  = sockServer.recvfrom(BUFFER_SIZE)
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
    sockServer.close()
    print('Servidor finalizado com sucesso.\n')
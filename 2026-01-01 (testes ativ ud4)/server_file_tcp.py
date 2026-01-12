import socket, os
from constantes import *
from funcoes import dir_Existe, unica_Conexao

os.system('cls') if os.name == 'nt' else os.system('clear')

#Inicializa o servidor e atende conexões sequencialmente (cada requisição em nova conexão).
#sockServer = None
try:
    sockServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockServer.bind(('', HOST_PORT))

    sockServer.listen(5)
    sockServer.settimeout(TIMEOUT_SOCKET)

    print('\n' + '-' * 100)
    print('SERVIDOR TCP Inicializado - Aguardando conexões...')
    print('Pressione CTRL+C para encerrar.')
    print(f'IP/Porta do Servidor: {(HOST_IP_SERVER, HOST_PORT)}')
    print('-' * 100 + '\n')

    dir_Existe(DIR_IMG_SERVER)

    while True:
        try:
            conexao, cliente = sockServer.accept()
            unica_Conexao(conexao, cliente)
        except socket.timeout:
            continue

except KeyboardInterrupt:
    print('\nAVISO: encerrando servidor...\n')
except socket.error as erro_Servidor:
    print(f'\nERRO DE SOCKET: {erro_Servidor}\n')
except Exception as erro:
    print(f'\nERRO GENÉRICO: {erro}\n')
finally:
    if sockServer:
        sockServer.close()
    print('Servidor finalizado com Sucesso...\n\n')

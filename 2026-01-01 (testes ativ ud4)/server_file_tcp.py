import socket
from constantes import *
from funcoes import dir_existe, unica_Conexao

"""Inicializa o servidor e atende conexões sequencialmente (cada requisição em nova conexão)."""
server = None
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', HOST_PORT))
    server.listen(5)
    print('\n' + '-' * 100)
    print('SERVIDOR TCP Inicializado - Aguardando conexões...')
    print('Pressione CTRL+C para encerrar.')
    print(f'IP/Porta do Servidor: {("", HOST_PORT)}')
    print('-' * 100 + '\n')

    dir_existe(DIR_IMG_SERVER)

    while True:
        conexao, cliente = server.accept()
        unica_Conexao(conexao, cliente)

except KeyboardInterrupt:
        print('\nAVISO: encerrando servidor...\n')
except socket.error as erro_Servidor:
        print(f'\nERRO DE SOCKET: {erro_Servidor}\n')
except Exception as erro:
        print(f'\nERRO GENÉRICO: {erro}\n')
finally:
    if server:
        try:
            server.close()
        except:
            pass

import socket
from constantes import *
from funcoes import ensure_dir, handle_connection

"""Inicializa o servidor e atende conexões sequencialmente (cada requisição em nova conexão)."""
server = None
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', HOST_PORT))
    server.listen(5)
    print('\n' + '-'*100)
    print('SERVIDOR TCP Inicializado - Aguardando conexões...')
    print('Pressione CTRL+C para encerrar.')
    print(f'IP/Porta do Servidor: {("", HOST_PORT)}')
    print('-'*100 + '\n')

    ensure_dir(DIR_IMG_SERVER)

    while True:
        conn, addr = server.accept()
        # atendimento sequencial (sem threads)
        handle_connection(conn, addr)

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

'''# Limpando a tela do terminal
os.system('cls') if os.name == 'nt' else os.system('clear')

try:
   # Criando um socket (IPv4 / UDP)
   sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   # Ligando o socket do servidor à porta
   sockServer.bind(('', HOST_PORT))

   # Definindo um timeout para o socket.
   sockServer.settimeout(TIMEOUT_SOCKET)

   # Mensagem de início do servidor
   print('\n' + '-'*100)
   print('SERVIDOR UDP Inicializado - Recebendo Comandos...')
   print('Pressione CTRL+C para sair do servidor...\n')
   print(f'IP/Porta do Servidor.:{TUPLA_SERVER}')
   print('-'*100 + '\n')
   
   while True:
      try:
         # Recebendo solicitações do cliente (fragmentos)
         byteFragmento, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)        
      except socket.timeout:
         continue
      else: 
        # Abrindo o arquivo para a enviar ao cliente
        strNomeArquivo = byteFragmento.decode(CODE_PAGE)
        print (f'Recebi pedido para o arquivo: {strNomeArquivo}')
        try:
           arqEnvio = open (f'{DIR_IMG_SERVER}\\{strNomeArquivo}', 'rb')
        except FileNotFoundError:
           print (f'Arquivo não encontrado: {strNomeArquivo}\n')
           strMensagemErro = 'ERRO: Arquivo não encontrado.'.encode(CODE_PAGE)
           sockServer.sendto(strMensagemErro, tuplaCliente)
           continue
        except Exception as strErro:
           print (f'Erro ao abrir o arquivo: {strErro}\n')
           strMensagemErro = f'ERRO: {strErro}'.encode(CODE_PAGE)
           sockServer.sendto(strMensagemErro, tuplaCliente)
           continue
        else:
           # Lendo o conteúdo do arquivo para enviar ao cliente
           print (f'Enviando arquivo: {strNomeArquivo}')
           sockServer.sendto(b'OK', tuplaCliente)
           fileData = arqEnvio.read(4096)
           sockServer.sendto(fileData, tuplaCliente)

        # Fechando o arquivo
        arqEnvio.close()

except KeyboardInterrupt:
   print('\nAVISO.........: Foi Pressionado CTRL+C...\nSaindo do Servidor...\n\n')
except socket.error as strErro:
   print(f'\nERRO DE SOCKET: {strErro}\n\n')
except Exception as strErro:
   print(f'\nERRO GENÉRICO..: {strErro}\n\n')
finally:
   # Fechando o Socket
   sockServer.close()
   print('Servidor finalizado com Sucesso...\n\n')'''
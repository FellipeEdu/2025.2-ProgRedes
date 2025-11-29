import socket
import os

HOST_IP_SERVER  = ''
HOST_PORT       = 50000
BUFFER_SIZE     = 1024
CODE_PAGE       = 'utf-8'

sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockServer.bind((HOST_IP_SERVER, HOST_PORT))
sockServer.settimeout(0.5)

print('\nRecebendo Mensagens...')
print('Pressione CTRL+C para sair do servidor...\n')
print('-'*100 + '\n')

try:
    while True:
        try:
            # --- Recebendo o nome do arquivo ---
            byteTamanhoNome, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            intTamanhoNome = int(byteTamanhoNome.decode(CODE_PAGE))

            byteNomeArquivo, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            strNomeArquivo = byteNomeArquivo.decode(CODE_PAGE)

            # --- Recebendo a mensagem ---
            byteTamanhoMensagem, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            intTamanhoMensagem = int(byteTamanhoMensagem.decode(CODE_PAGE))

            byteMensagem, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            strMensagem = byteMensagem.decode(CODE_PAGE)

        except socket.timeout:
            continue
        else:
            # Nome do host do cliente
            try:
                strNomeHost = socket.gethostbyaddr(tuplaCliente[0])[0].split('.')[0].upper()
            except:
                strNomeHost = tuplaCliente[0]

            print(f'{tuplaCliente} -> {strNomeHost}')
            print(f'Arquivo solicitado: {strNomeArquivo}')
            print(f'Mensagem recebida: {strMensagem}')

            # --- Abrindo o arquivo ---
            if os.path.exists(strNomeArquivo):
                try:
                    with open(strNomeArquivo, 'r', encoding=CODE_PAGE, errors='replace') as f:
                        conteudo = f.read()
                    resposta = conteudo.encode(CODE_PAGE)
                except Exception as e:
                    resposta = f'Erro ao abrir arquivo: {e}'.encode(CODE_PAGE)
            else:
                resposta = f'Arquivo "{strNomeArquivo}" não encontrado.'.encode(CODE_PAGE)

            # --- Enviando tamanho ---
            sockServer.sendto(str(len(resposta)).encode(CODE_PAGE), tuplaCliente)

            # --- Enviando conteúdo ---
            sockServer.sendto(resposta, tuplaCliente)

except KeyboardInterrupt:
    print('\nAVISO: CTRL+C pressionado.\nSaindo...\n')
finally:
    sockServer.close()
    print('Servidor finalizado.\n')
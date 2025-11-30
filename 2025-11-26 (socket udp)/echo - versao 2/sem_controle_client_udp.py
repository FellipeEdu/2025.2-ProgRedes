import socket, os.path

# ----------------------------------------------------------------------
HOST_IP_SERVER = '192.168.1.2' # Definindo o IP do servidor
HOST_PORT      = 50000       # Definindo a porta
TUPLA_SERVER   = (HOST_IP_SERVER, HOST_PORT)

BUFFER_SIZE    = 1024 * 5        # Tamanho do buffer definido em 5kb
CODE_PAGE      = 'utf-8'     # Definindo a página de 
                             # codificação de caracteres
DIRETORIO      = os.path.dirname(__file__)
# ----------------------------------------------------------------------

# Criando o socket (socket.AF_INET -> IPV4 / socket.SOCK_DGRAM -> UDP)
sockClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sockClient.settimeout(5.0) # Dá 5 segundos para o servidor responder

print('\n----- Cliente de Arquivos -----\n')

while True:
    strNomeArquivo = input('Digite o nome do arquivo (ou SAIR): ')

    if strNomeArquivo.lower().strip() == 'sair': break
    # envia requisição
    sockClient.sendto(strNomeArquivo.encode(CODE_PAGE), TUPLA_SERVER)
    print(f"Solicitação enviada para o arquivo '{strNomeArquivo}'...")

    try:
        bytesStatus, tuplaOrigem = sockClient.recvfrom(BUFFER_SIZE)
        strStatus = bytesStatus.decode(CODE_PAGE)
        
        if strStatus.startswith('ERRO'):
            print(f'Servidor retornou um erro: {strStatus}\n')
            continue
            
        if strStatus != 'OK_PRONTO_PARA_RECEBER':
            print(f'Erro de protocolo. Recebido: {strStatus}\n')
            continue

        print('\nConexão estabelecida. Iniciando recebimento...')

        # recebendo e salvando
        nomeArqLocal = f'{DIRETORIO}/BAIXADO_{strNomeArquivo}'
        pacotesRecebidos = 0
        ultimoPacote = 0

        with open(nomeArqLocal, 'wb') as arquivo:
            while True:
                try:
                    bytesPacote, tuplaOrigem = sockClient.recvfrom(BUFFER_SIZE)

                    if bytesPacote == b'FIM_TRANSFERENCIA':
                        break

                    # extraindo cabeçalho e dados
                    # Procura o primeiro ':' para separar a numeração
                    try:
                        pacotesRecebidos += 1
                        cabecalho, bytesDados = bytesPacote.split(b':', 1)
                        numeroPacote = int(cabecalho.decode(CODE_PAGE))
                        
                        # checagem de ordem (para ignorar duplicatas ou pacotes fora de ordem)
                        if numeroPacote == ultimoPacote + 1:
                            arquivo.write(bytesDados)
                            ultimoPacote = numeroPacote
                            
                            if pacotesRecebidos % 10 == 0:
                                print(f'Pacote #{numeroPacote} recebido e gravado...')
                        
                    except ValueError:
                        # Pacote com formato inválido ou 'FIM'
                        if bytesPacote != b'FIM_TRANSFERENCIA':
                            print("AVISO: Pacote inválido ou fora de ordem ignorado.")
                        pass # vai continuar o loop

                except socket.timeout: break

        print(f'\n----- SUCESSO -----')
        print(f"Arquivo '{strNomeArquivo}' salvo localmente como '{nomeArqLocal}'.")
        print(f'Total de pacotes processados: {ultimoPacote}\n')

    except socket.timeout:
        print('Erro: Timeout. Servidor não respondeu à requisição inicial.\n')

# Fechando o socket
sockClient.close()
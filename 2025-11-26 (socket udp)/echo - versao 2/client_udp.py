import socket, os.path, time

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
            
        if strStatus != 'OK_PRONTO':
            print(f'Erro de protocolo. Recebido: {strStatus}\n')
            continue

        print('\nConexão estabelecida. Iniciando recebimento...')

        # recebendo e salvando
        nomeArqLocal = f'{DIRETORIO}\\BAIXADO_controle_{strNomeArquivo}'
        pacotesRecebidos = 0
        ultimoPacote = 0

        with open(nomeArqLocal, 'wb') as arquivo:
            while True:
                try:
                    bytesPacote, tuplaOrigem = sockClient.recvfrom(BUFFER_SIZE)

                    # TRATAMENTO DE FIM
                    if bytesPacote == b'FIM_TRANSFERENCIA':
                        sockClient.sendto(b'FIM_ACK', TUPLA_SERVER) 
                        break

                    # EXTRAI CABEÇALHO E DADOS
                    try:
                        cabecalho, bytesDados = bytesPacote.split(b':', 1)
                        numPacote = int(cabecalho.decode(CODE_PAGE))
                        
                        pacotesRecebidos += 1
                        
                        # Pacote Corretamente em Ordem
                        if numPacote == ultimoPacote + 1:
                            arquivo.write(bytesDados)
                            ultimoPacote = numPacote
                            
                            # Envia ACK para o servidor
                            ackMsg = f'ACK:{numPacote}'.encode(CODE_PAGE)
                            sockClient.sendto(ackMsg, TUPLA_SERVER)
                            
                            if ultimoPacote % 100 == 0: print(f'Pacote #{ultimoPacote} ACK enviado...')

                        # Pacote Duplicado (Reenvio)
                        elif numPacote <= ultimoPacote:
                            # O pacote foi retransmitido pelo servidor. Reenvia o ACK do último pacote salvo.
                            ackMsg = f'ACK:{ultimoPacote}'.encode(CODE_PAGE)
                            sockClient.sendto(ackMsg, TUPLA_SERVER)
                            # Não escreve o dado
                            
                        # Pacote Perdido (Fora de Ordem e não é reenvio)
                        else:
                             # O cliente espera pelo pacote correto (que foi perdido)
                             # O servidor vai atingir o timeout e retransmitir o pacote correto.
                             print(f'AVISO: Pacote #{numPacote} fora de ordem. Esperando #{ultimoPacote + 1}.')
                             
                    except ValueError:
                        pass # Pacote inválido ignorado

                except socket.timeout:
                    print('\nTimeout: Servidor não enviou mais dados. Tentando novamente...')
                    break
                        
        print(f'\n----- SUCESSO -----')
        print(f"Arquivo '{strNomeArquivo}' salvo localmente como '{nomeArqLocal}'")
        print(f'Total de pacotes processados: {ultimoPacote}\n')

    except socket.timeout:
        print('Erro: Timeout. Servidor não respondeu à requisição inicial.\n')

# Fechando o socket
sockClient.close()
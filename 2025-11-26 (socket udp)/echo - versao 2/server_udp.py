import socket, os.path, time

# ----------------------------------------------------------------------
HOST_IP_SERVER  = ''              # Definindo o IP do servidor
HOST_PORT       = 50000           # Definindo a porta
BUFFER_SIZE     = 1024              # Tamanho do buffer
CODE_PAGE       = 'utf-8'         # Definindo a página de 
                                  # codificação de caracteres
DIR_CODIGO      = os.path.dirname(__file__)
DIR_PAI         = os.path.dirname(DIR_CODIGO)
DIRETORIO       = os.path.join(DIR_PAI, 'file_server') 
# ----------------------------------------------------------------------

# Criando o socket (socket.AF_INET -> IPV4 / socket.SOCK_DGRAM -> UDP)
sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Ligando o socket à porta
sockServer.bind( (HOST_IP_SERVER, HOST_PORT) ) 

# Definindo um timeout (tempo de vida) para o socket
sockServer.settimeout(1.0)

print('\nRecebendo Arquivos...')
print('Pressione CTRL+C para sair do servidor...\n')
print('-' * 70)

try:
    while True:
        try:
            # Recebendo os dados do cliente
            byteRequisicao, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            strNomeArquivo = byteRequisicao.decode(CODE_PAGE).strip()
            
            print(f"Requisição recebida de {tuplaCliente} para arquivo '{strNomeArquivo}'")
            
        except socket.timeout: continue

        caminhoArq = os.path.join(DIRETORIO, strNomeArquivo)

        if not os.path.exists(caminhoArq):
            print(f'AVISO: Arquivo "{strNomeArquivo}" não encontrado.\n{'*' * 50}')
            sockServer.sendto(b'ERRO: ARQUIVO NAO ENCONTRADO', tuplaCliente)
            continue
            
        print(f'Iniciando transferência de: {strNomeArquivo}')

        # LEITURA E ENVIO DO ARQUIVO EM CHUNKS (PEDAÇOS)
        try:
            sockServer.sendto(b'OK_PRONTO', tuplaCliente)

            with open(caminhoArq, 'rb') as arquivo:
                numPacote = 0
                retransmitir = False
                posicaoAnterior = 0

                while True: 
                    try:
                        # 3a. Ler o próximo pedaço (só se não for retransmissão)
                        if numPacote == 0 or not retransmitir:                              
                            # Guarda a posição atual para retransmissão
                            posicaoAnterior = arquivo.tell()
                            bytesDados = arquivo.read(BUFFER_SIZE - 20)
                            
                            if not bytesDados:
                                break # Fim do arquivo
                                
                            numPacote += 1
                                    
                            cabecalho = f'{numPacote}:'.encode(CODE_PAGE)
                            pacoteCompleto = cabecalho + bytesDados
                                
                            # 3b. Envia o pacote
                        sockServer.sendto(pacoteCompleto, tuplaCliente)
                            
                            # 3c. Espera pelo ACK
                        bytesAck, _ = sockServer.recvfrom(BUFFER_SIZE) 
                        strAck = bytesAck.decode(CODE_PAGE)
                            
                            # Confirma se o ACK é do pacote correto
                        if strAck == f'ACK:{numPacote}':
                            if numPacote % 100 == 0: print(f'Pacote #{numPacote} ACK recebido. Próximo...')
                            retransmitir = False # Avança para o próximo pacote

                        else:
                            # ACK inválido/duplicado. Reenvia o pacote atual.
                            print(f'AVISO: ACK inválido/duplicado ({strAck}). Reenviando #{numPacote}.')
                            retransmitir = True
                            arquivo.seek(posicaoAnterior) # Volta o ponteiro para re-leitura
                    except:
                        # Timeout: Pacote ou ACK perdido. Reenvia o pacote atual.
                        print(f'TIMEOUT ao esperar ACK #{numPacote}. Reenviando.')
                        retransmitir = True
                        arquivo.seek(posicaoAnterior) # Volta o ponteiro para re-leitura
                    
                for _ in range(5): 
                    sockServer.sendto(b'FIM_TRANSFERENCIA', tuplaCliente)
                    try:
                        bytesAckFim, _ = sockServer.recvfrom(BUFFER_SIZE)
                        if bytesAckFim == b'FIM_ACK': break

                    except socket.timeout:
                        print('Timeout no ACK FIM. Tentando novamente.')
                        
                    print(f'Arquivo enviado em {numPacote} pacotes.')
                    print(f'Transferência finalizada para {strNomeArquivo}.\n{'*' * 50}')
                    
        except Exception as erro:
            print(f'ERRO ao ler/enviar arquivo: {erro}')
            sockServer.sendto(f'ERRO INTERNO: {erro}'.encode(CODE_PAGE), tuplaCliente)


except KeyboardInterrupt:
   print('\nAVISO: Foi Pressionado CTRL+C...\nSaindo do Servidor...\n\n')
finally:
   # Fechando o socket
   sockServer.close()
   print('Servidor finalizado com sucesso...\n\n')
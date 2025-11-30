import socket, os.path

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
print('-'*70 + '\n')

try:
    while True:
        try:
            # Recebendo os dados do cliente
            byteRequisicao, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            strNomeArquivo = byteRequisicao.decode(CODE_PAGE).strip()
            #intTamanhoMensagem = int(byteMensagem.decode(CODE_PAGE))
            print(f"Requisição recebida de {tuplaCliente} para arquivo '{strNomeArquivo}'")

            #if intTamanhoMensagem > BUFFER_SIZE: BUFFER_SIZE = intTamanhoMensagem

            #byteMensagem, tuplaCliente = sockServer.recvfrom(BUFFER_SIZE)
            
        except socket.timeout: continue

        caminhoArq = os.path.join(DIRETORIO, strNomeArquivo)

        if not os.path.exists(caminhoArq):
            print(f'AVISO: Arquivo "{strNomeArquivo}" não encontrado no caminho {caminhoArq}.')
            sockServer.sendto(b'ERRO: ARQUIVO NAO ENCONTRADO', tuplaCliente)
            continue
            
        print(f'Iniciando transferência de: {strNomeArquivo}')
        sockServer.sendto(b'OK_PRONTO_PARA_RECEBER', tuplaCliente) # Sinaliza que vai começar

        # LEITURA E ENVIO DO ARQUIVO EM CHUNKS (PEDAÇOS)
        try:
            with open(caminhoArq, 'rb') as arquivo:
                intNumPacote = 0
                while True:
                    bytesDados = arquivo.read(BUFFER_SIZE - 20) # Reserva espaço para o cabeçalho (numeração)
                    
                    if not bytesDados: break 
                    
                    intNumPacote += 1
                    
                    # Cria um cabeçalho simples: NÚMERO_PACOTE:
                    cabecalho = f'{intNumPacote}:'.encode(CODE_PAGE)
                    pacoteCompleto = cabecalho + bytesDados
                    
                    sockServer.sendto(pacoteCompleto, tuplaCliente)
                    
                    # Pequena pausa para evitar sobrecarga (fluxo UDP)
                    #sleep(0.0001) 
                    
                print(f'\nArquivo enviado em {intNumPacote} pacotes.')
                
                # ENVIA SINAL DE FIM
                sockServer.sendto(b'FIM_TRANSFERENCIA', tuplaCliente)
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
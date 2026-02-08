import socket, struct, json, os, platform, threading
import psutil
from funcoes_bot import *

os.system('cls' if platform.system() == 'Windows' else 'clear')

# 1. Cria a lista vazia que vai guardar os dados
lstMeuHistorico = []

# 2. Inicia a thread passando a lista como argumento
# Usamos daemon=True para que ela feche se você fechar o Agente
threading.Thread(target=thread_coletar_cpu, args=(lstMeuHistorico,), daemon=True).start()

print('\nAGENTE DE MONITORAMENTO - Iniciando...')
print('Pressione Ctrl+C para encerrar o Agente')
print('---------------------------------------\n')

strIPGerente = input('Digite o IP da estação de gerência: ')

# Validação simples: se o usuário não digitar nada, assume o localhost (para testes)
if not strIPGerente:
    strIPGerente = '127.0.0.1'
    print(f'Nenhum IP informado. Usando padrão: {strIPGerente}')

intPorta = 45678

# Try principal -> Captura de exceções de conexão e encerramento
try:
    objSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'Conectando ao Gerente em {strIPGerente}:{intPorta}...')
    objSocket.connect((strIPGerente, intPorta))
    print('Conexão estabelecida com sucesso!\n')

    # Loop infinito -> Aguardando pedidos do Gerente
    while True:
        try:
            # Recebe o comando (Mínimo 1 byte para a letra)
            bytesDadosRecebidos = objSocket.recv(1024)
            
            if not bytesDadosRecebidos:
                print('Conexão encerrada pelo Gerente.')
                break

            strComando = bytesDadosRecebidos[0:1].decode('utf-8')
            dictResposta = {}

            # Processando os comandos baseados na tabela
            if strComando == 'G': # Geral (Processos)
                dictResposta = comando_procs() 

            elif strComando == 'P': # Processo Específico
                dictResposta = comando_proc(bytesDadosRecebidos)

            elif strComando == 'H': # Hardware
                dictResposta = {    
                    "so": platform.system(),
                    "arch": platform.machine(),
                    "cpu_cores": psutil.cpu_count(),
                    "mem_total": round(psutil.virtual_memory().total / (1024**2), 2),
                    "nome_pc": platform.node()
                }

            elif strComando == 'T':
                dictResposta = {"historico": lstMeuHistorico}

            # --- PREPARANDO A RESPOSTA ---
            # Converte para JSON e gera os bytes
            strJSON     = json.dumps(dictResposta)
            bytesPayload  = strJSON.encode('utf-8')
            
            # Cabeçalho com o tamanho em Big Endian (4 bytes)
            binTamanho  = struct.pack('>I', len(bytesPayload))

            # Envia o pacote completo (Tamanho + JSON)
            objSocket.sendall(binTamanho + bytesPayload)
            print(f'Comando [{strComando}] processado e enviado.')

        except struct.error:
            print('Aviso: Recebida mensagem malformada. Ignorando...')
            continue

except KeyboardInterrupt:
    print('\n\nEncerrando o Agente...')
except Exception as erro:
    print(f'\n\nERRO: {erro}')
finally:
    objSocket.close()
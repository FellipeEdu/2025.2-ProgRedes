import socket
import struct
import json
import psutil
import os
import platform

# Limpando a tela conforme o estilo do professor
os.system('cls' if platform.system() == 'Windows' else 'clear')

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
            binDadosRecebidos = objSocket.recv(1024)
            
            if not binDadosRecebidos:
                print('Conexão encerrada pelo Gerente.')
                break

            strComando = binDadosRecebidos[0:1].decode('utf-8')
            dictResposta = {}

            # Processando os comandos baseados na tabela
            if strComando == 'H': # Hardware
                dictResposta = {
                    "cpu_cores": psutil.cpu_count(),
                    "mem_total": round(psutil.virtual_memory().total / (1024**2), 2),
                    "so": platform.system(),
                    "arch": platform.machine(),
                    "node": platform.node()
                }

            elif strComando == 'G': # Geral (Processos)
                lstProcessos = []
                for p in psutil.process_iter(['pid', 'name']):
                    lstProcessos.append(p.info)
                dictResposta = lstProcessos

            elif strComando == 'P': # Processo Específico
                intPID = struct.unpack('>I', binDadosRecebidos[1:5])[0]
                try:
                    p = psutil.Process(intPID)
                    dictResposta = {
                        "ok": True,
                        "pid": p.pid,
                        "nome": p.name(),
                        "path": p.exe(),
                        "mem": round(p.memory_info().rss / (1024**2), 2),
                        "cpu": p.cpu_percent(interval=0.1)
                    }
                except psutil.NoSuchProcess:
                    dictResposta = {"ok": False}

            # --- PREPARANDO A RESPOSTA ---
            # Converte para JSON e gera os bytes
            strJSON     = json.dumps(dictResposta)
            binPayload  = strJSON.encode('utf-8')
            
            # Cabeçalho com o tamanho em Big Endian (4 bytes)
            binTamanho  = struct.pack('>I', len(binPayload))

            # Envia o pacote completo (Tamanho + JSON)
            objSocket.sendall(binTamanho + binPayload)
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
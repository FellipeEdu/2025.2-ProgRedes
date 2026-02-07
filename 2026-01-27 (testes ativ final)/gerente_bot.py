import os, sys, requests, platform, json, socket, threading, struct
from token_bot import *
from funcoes_bot import *

# Dicionário global para monitorar agentes { "IP": objeto_socket }
dictAgentes = {}

# --- FUNÇÃO PARA COMUNICAÇÃO COM O AGENTE (PROTOCOL RAIZ) ---
def requisitar_agente(objSocketAgente, strComando, intPID=None):
    try:
        # Envio: Letra do comando (e PID se for o caso)
        if strComando == 'P' and intPID is not None:
            binPacote = strComando.encode('utf-8') + struct.pack('>I', intPID)
            objSocketAgente.sendall(binPacote)
        else:
            objSocketAgente.sendall(strComando.encode('utf-8'))

        # Recebimento Etapa 1: Tamanho (4 bytes Big Endian)
        binTamanho = objSocketAgente.recv(4)
        if not binTamanho: return None
        intTamanho = struct.unpack('>I', binTamanho)[0]

        # Recebimento Etapa 2: JSON (Leitura em chunks/pedaços)
        binPayload = b''
        while len(binPayload) < intTamanho:
            binPayload += objSocketAgente.recv(min(intTamanho - len(binPayload), 4096))
        
        return json.loads(binPayload.decode('utf-8'))
    except:
        return None

# --- THREAD: AGUARDAR CONEXÃO DE NOVOS AGENTES ---
def thread_aguardar_agentes():
    objSocketServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    objSocketServidor.bind(('0.0.0.0', 45678))
    objSocketServidor.listen(10)
    
    while True:
        objSocketAgente, addr = objSocketServidor.accept()
        strIPAgente = addr[0]
        dictAgentes[strIPAgente] = objSocketAgente
        print(f"\n[NOVO AGENTE] Online: {strIPAgente}")

# --- CONFIGURAÇÃO INICIAL DO TELEGRAM ---
strURLBase = f'https://api.telegram.org/bot{API_TOKEN}'
strURLGetUpdates = f'{strURLBase}/getUpdates'
strURLSendMessage = f'{strURLBase}/sendMessage'

os.system('cls' if platform.system() == 'Windows' else 'clear')
print('GERENTE - Aguardando comandos e agentes...')

# Inicia a thread de escuta dos agentes (Daemon para fechar junto com o script)
threading.Thread(target=thread_aguardar_agentes, daemon=True).start()

intIDUltimaAtualizacao = 0

# --- LOOP PRINCIPAL (MODO PASSIVO TELEGRAM) ---
try:
    while True:
        try:
            reqURL = requests.get(strURLGetUpdates, 
                                  params={'offset': intIDUltimaAtualizacao + 1, 'timeout': 20}, 
                                  timeout=25)
        except requests.Timeout:
            continue
        
        if reqURL.status_code == 200:
            jsonRetorno = json.loads(reqURL.text)
            
            for atualizacao in jsonRetorno["result"]:
                intIDUltimaAtualizacao = atualizacao["update_id"]
                if 'message' not in atualizacao: continue
                
                intIDChat = atualizacao["message"]["chat"]["id"]
                strMensagem = atualizacao["message"].get("text", "")
                
                # Processamento do Comando
                lstPartes = strMensagem.split()
                strCmd = lstPartes[0].lower() if len(lstPartes) > 0 else ""
                strResposta = "Comando inválido ou incompleto."

                # LÓGICA DOS COMANDOS
                if strCmd == "/start":
                    strResposta = startBot()

                if strCmd == "/agentes":
                    strResposta = "Agentes conectados:\n" + ("\n".join(dictAgentes.keys()) if dictAgentes else "Nenhum")

                elif strCmd in ["/hardw", "/procs", "/topcpu", "/topmem"]:
                    if len(lstPartes) > 1:
                        strIP = lstPartes[1]
                        if strIP in dictAgentes:
                            # Mapeia comando Telegram -> Letra do Protocolo
                            mapa = {"/hardw":'H', "/procs":'G', "/topcpu":'C', "/topmem":'M'}
                            dictDados = requisitar_agente(dictAgentes[strIP], mapa[strCmd])
                            strResposta = f"Dados de {strIP}:\n{json.dumps(dictDados, indent=2)}"
                        else:
                            strResposta = "IP do Agente não encontrado."
                    else:
                        strResposta = "Uso: /comando [IP]"

                elif strCmd == "/proc": # Requer IP e PID
                    if len(lstPartes) > 2:
                        strIP, intPID = lstPartes[1], int(lstPartes[2])
                        if strIP in dictAgentes:
                            dictDados = requisitar_agente(dictAgentes[strIP], 'P', intPID)
                            strResposta = f"Processo {intPID} em {strIP}:\n{json.dumps(dictDados, indent=2)}"
                    else:
                        strResposta = "Uso: /proc [IP] [PID]"

                # Envio da Resposta ao Telegram
                requests.post(strURLSendMessage, data={'chat_id': intIDChat, 'text': strResposta})

except KeyboardInterrupt:
    sys.exit('\nEncerrando Gerente...\n')
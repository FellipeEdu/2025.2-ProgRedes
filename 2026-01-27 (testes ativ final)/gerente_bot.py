import os, sys, requests, platform, json, socket, threading, struct
from token_bot import *
from funcoes_bot import *

dictAgentes = {}

mapa_protocolo = {
    "/procs":'G', 
    "/proc":'P',
    "/topcpu":'C',
    "/topmem":'M', 
    "/hardw":'H', 
    "/histcpu":'T'
    }
'''
def requisitar_agente(objSocketAgente, strComando, intPID=None):
    try:
        objSocketAgente.settimeout(3.0) 
        if strComando == 'P' and intPID is not None:
            objSocketAgente.sendall(strComando.encode('utf-8') + struct.pack('>I', intPID))
        else:
            objSocketAgente.sendall(strComando.encode('utf-8'))

        bytesTamanho = objSocketAgente.recv(4)
        if not bytesTamanho: return {"erro": "Desconectado"}
        intTamanho = struct.unpack('>I', bytesTamanho)[0]

        bytesPayload = b''
        while len(bytesPayload) < intTamanho:
            chunk = objSocketAgente.recv(min(intTamanho - len(bytesPayload), 4096))
            if not chunk: break
            bytesPayload += chunk
        
        objSocketAgente.settimeout(None) 
        return json.loads(bytesPayload.decode('utf-8'))
    except:
        return {"erro": "Timeout ou falha"}

def thread_aguardar_agentes():
    objSocketServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    objSocketServidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Evita porta presa
    objSocketServidor.bind(('0.0.0.0', 45678))
    objSocketServidor.listen(10)
    while True:
        objSocketAgente, addr = objSocketServidor.accept()
        dictAgentes[addr[0]] = objSocketAgente
'''
strURLBase = f'https://api.telegram.org/bot{API_TOKEN}'
strURLGetUpdates = f'{strURLBase}/getUpdates'
strURLSendMessage = f'{strURLBase}/sendMessage'

os.system('cls' if platform.system() == 'Windows' else 'clear')
print('GERENTE - Aguardando comandos e agentes...')

threading.Thread(target=thread_aguardar_agentes, args=(dictAgentes,), daemon=True).start()

intIDUltimaAtualizacao = 0

msgStart = ("Bem-vindo ao BOT SHOW METRICS CNAT\n\n "
        "Este é um bot para consultar métricas de performance dos dispositivos conectados.\n\n "
        "```/?``` → Exibe mensagem de ajuda.\n\n"
        "```/start``` → Reexibe esta mensagem.")

while True:
    try:
        reqURL = requests.get(strURLGetUpdates, 
                         params={'offset': intIDUltimaAtualizacao + 1, 'timeout': 20}, timeout=25)
        if reqURL.status_code != 200: continue
        
        for atualizacao in reqURL.json().get("result", []):
            intIDUltimaAtualizacao = atualizacao["update_id"]
            if 'message' not in atualizacao: continue
            
            intIDChat = atualizacao["message"]["chat"]["id"]
            lstPartes = atualizacao["message"].get("text", "").split()
            if not lstPartes: continue
            
            strComando = lstPartes[0].lower()
            
            # COMANDOS SIMPLES
            if strComando == "/start": strResposta = startBot()
            elif strComando == "/agentes": strResposta = mostrarAgentes(dictAgentes)

            # COMANDOS QUE DEPENDEM DO AGENTE
            elif strComando in mapa_protocolo:
                if len(lstPartes) > 1:
                    strIP = lstPartes[1]
                    if strIP in dictAgentes:
                        # Requisição
                        pid = int(lstPartes[2]) if strComando == "/proc" and len(lstPartes) > 2 else None

                        dados = requisitar_agente(dictAgentes[strIP], mapa_protocolo[strComando], pid)
                        
                        if "erro" in dados: strResposta = f"❌ {dados['erro']}"
                        elif strComando == "/hardw":   strResposta = formatar_hardware(dados, strIP)
                        elif strComando == "/procs":   strResposta = formatar_processos(dados, strIP)
                        elif strComando == "/histcpu": strResposta = formatar_historico(dados, strIP)
                        elif strComando == "/proc":    strResposta = formatar_proc(dados, pid) #strResposta = f"Detalhes PID {pid}:\n```json\n{json.dumps(dados, indent=2)}```"
                    else: strResposta = "❌ Agente Offline."
                else: strResposta = "Uso: `/comando [IP]`"
            else: strResposta = "?? Comando desconhecido."

            requests.post(strURLSendMessage, 
                          data={'chat_id': intIDChat, 'text': strResposta, 'parse_mode': 'Markdown'})
    except KeyboardInterrupt:
        sys.exit('\n\nEncerrando o BOT Telegram...\n')
    except Exception as erro:
        print(f'\n\nERRO: {erro}')


'''import os, sys, requests, platform, json, socket, threading, struct
from token_bot import *
from funcoes_bot import *

# Dicionário global para monitorar agentes { "IP": objeto_socket }
dictAgentes = {}

# Mapa protocolos
mapa_protocolo = {
    "/procs": 'G',
    "/proc": 'P',
    "/topcpu": 'C', 
    "/topmem": 'M',
    "/hardw": 'H', 
    "/histcpu": 'T'
}

# --- FUNÇÃO PARA COMUNICAÇÃO COM O AGENTE (PROTOCOL RAIZ) ---
def requisitar_agente(objSocketAgente, strComando, intPID=None):
    try:
        # Define 3 segundos de limite. Se o agente sumir, o bot não trava.
        objSocketAgente.settimeout(3.0) 

        # Envio do Comando
        if strComando == 'P' and intPID is not None:
            bytesPacote = strComando.encode('utf-8') + struct.pack('>I', intPID)
            objSocketAgente.sendall(bytesPacote)
        else:
            objSocketAgente.sendall(strComando.encode('utf-8'))

        # Recebimento do Tamanho
        bytesTamanho = objSocketAgente.recv(4)
        if not bytesTamanho: 
            return {"erro": "Agente desconectado"}
        intTamanho = struct.unpack('>I', bytesTamanho)[0]

        # Recebimento do JSON (Garantindo que pega tudo)
        bytesPayload = b''
        while len(bytesPayload) < intTamanho:
            chunk = objSocketAgente.recv(min(intTamanho - len(bytesPayload), 4096))
            if not chunk: break
            bytesPayload += chunk
        
        # IMPORTANTE: Desativa o timeout para não afetar outras operações
        objSocketAgente.settimeout(None) 
        
        return json.loads(bytesPayload.decode('utf-8'))

    except socket.timeout:
        return {"erro": "O Agente demorou muito para responder."}
    except Exception as erro:
        return {"erro": f"Erro de comunicação: {erro}"}

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
                strComando = lstPartes[0].lower() if len(lstPartes) > 0 else ""
                strResposta = "Comando inválido ou incompleto."

                # LÓGICA DOS COMANDOS
                if strComando == "/start":
                    strResposta = startBot()

                elif strComando == "/agentes":
                    strResposta = "Agentes conectados:\n" + ("\n".join(dictAgentes.keys()) if dictAgentes else "Nenhum")
                # G, P, C, M, H
                    
                    ###
                    elif strComando == "/procs":
                        if len(lstPartes) > 1:
                            strIP = lstPartes[1]
                            if strIP in dictAgentes:
                                dictDados = requisitar_agente(dictAgentes[strIP], 'G')
                                if dictDados and 'processos' in dictDados:
                                    # Pegamos apenas os 10 primeiros para não estourar o limite do Telegram
                                    top_procs = dictDados['processos'][:10] 
                                    
                                    strResposta = f"📝 **Top 10 Processos em {strIP}:**\n```\n"
                                    strResposta += f"{'PID':<7} | {'NOME':<20}\n"
                                    for p in top_procs:
                                        strResposta += f"{p['pid']:<7} | {p['nome'][:20]:<20}\n"
                                    strResposta += "```"
                                else:
                                    strResposta = "⚠️ Erro ao listar processos."
                            else:
                                strResposta = "IP do Agente não encontrado."
                        else: 
                            strResposta = "Uso: /comando [IP]"
                    ###

                elif strComando in mapa_protocolo:
                    if len(lstPartes) > 1:
                        strIP = lstPartes[1]
                        if strIP in dictAgentes:
                            # Pega a letra correta usando o comando digitado
                            letra = mapa_protocolo[strComando]
                            dictDados = requisitar_agente(dictAgentes[strIP], letra)
                            
                            # Aqui você pode colocar aquela lógica bonita que conversamos
                            if strComando == "/histcpu":
                                if dictDados and "historico" in dictDados:
                                    lstHist = dictDados["historico"]
                                    
                                    # Vamos montar um visual legal com barrinhas
                                    strSaida = f"📊 **Histórico de CPU (Último Minuto) - {strIP}**\n\n"
                                    
                                    for i, valor in enumerate(lstHist):
                                        # Calcula o tempo (0s, 5s, 10s...)
                                        intSegundos = i * 5
                                        
                                        # Cria a barra visual (cada quadrado vale 10%)
                                        intBarras = int(valor / 10)
                                        strBarraVisual = "■" * intBarras + "□" * (10 - intBarras)
                                        
                                        strSaida += f"`{intSegundos:02d}s | {strBarraVisual} {valor:>5.1f}%` \n"
                                    
                                    strResposta = strSaida
                                else:
                                    strResposta = "⚠️ O Agente ainda não coletou dados suficientes ou deu erro."
                            
                            elif strComando == "/proc": # Requer IP e PID
                                if len(lstPartes) > 2:
                                    strIP, intPID = lstPartes[1], int(lstPartes[2])
                                    if strIP in dictAgentes:
                                        dictDados = requisitar_agente(dictAgentes[strIP], 'P', intPID)
                                        strResposta = f"Processo {intPID} em {strIP}:\n{json.dumps(dictDados, indent=2)}"
                                else:
                                    strResposta = "Uso: /proc [IP] [PID]"
                            
                            else:
                                strResposta = f"Dados de {strIP}:\n{json.dumps(dictDados, indent=2)}"
                        else:
                            strResposta = "IP do Agente não encontrado."
                    else:
                        strResposta = "Uso: /comando [IP]"
                # P
                
                elif strComando == "/histcpu":
                    if len(lstPartes) > 1:
                        strIP = lstPartes[1]
                        if strIP in dictAgentes:
                            # Envia a letra 'T' para o Agente buscar a lista lstMeuHistorico
                            dictDados = requisitar_agente(dictAgentes[strIP], 'H_CPU')
                            
                            if dictDados and "historico" in dictDados:
                                lstHist = dictDados["historico"]
                                
                                # Vamos montar um visual legal com barrinhas
                                strSaida = f"📊 **Histórico de CPU (Último Minuto) - {strIP}**\n\n"
                                
                                for i, valor in enumerate(lstHist):
                                    # Calcula o tempo (0s, 5s, 10s...)
                                    intSegundos = i * 5
                                    
                                    # Cria a barra visual (cada quadrado vale 10%)
                                    intBarras = int(valor / 10)
                                    strBarraVisual = "■" * intBarras + "□" * (10 - intBarras)
                                    
                                    strSaida += f"`{intSegundos:02d}s | {strBarraVisual} {valor:>5.1f}%` \n"
                                
                                strResposta = strSaida
                            else:
                                strResposta = "⚠️ O Agente ainda não coletou dados suficientes ou deu erro."
                        else:
                            strResposta = "❌ Esse IP de Agente não está conectado."
                    else:
                        strResposta = "💡 Uso correto: `/histcpu [IP]`"
                
                # Envio da Resposta ao Telegram
                requests.post(strURLSendMessage, data={'chat_id': intIDChat, 'text': strResposta, 'parse_mode': 'Markdown'})

except KeyboardInterrupt:
    sys.exit('\nEncerrando Gerente...\n')
'''
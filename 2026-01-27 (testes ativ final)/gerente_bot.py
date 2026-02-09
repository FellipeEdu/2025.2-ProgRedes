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

strURLBase = f'https://api.telegram.org/bot{API_TOKEN}'
strURLGetUpdates = f'{strURLBase}/getUpdates'
strURLSendMessage = f'{strURLBase}/sendMessage'

os.system('cls' if platform.system() == 'Windows' else 'clear')
print('GERENTE - Aguardando comandos e agentes...')

threading.Thread(target=thread_aguardar_agentes, args=(dictAgentes,), daemon=True).start()

intIDUltimaAtualizacao = 0

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
            if strComando == "/start":      strResposta = startBot()
            elif strComando == "/?":        strResposta = ajudaBot()
            elif strComando == "/agentes":  strResposta = mostrarAgentes(dictAgentes)

            # COMANDOS QUE DEPENDEM DO AGENTE
            elif strComando in mapa_protocolo:
                if len(lstPartes) > 1:
                    strIP = lstPartes[1]
                    if strIP in dictAgentes:
                        # Requisição
                        pid = int(lstPartes[2]) if strComando == "/proc" and len(lstPartes) > 2 else None

                        dados = requisitar_agente(dictAgentes[strIP], mapa_protocolo[strComando], pid)
                        
                        if "erro" in dados: strResposta = f"{dados['erro']}"
                        elif strComando == "/hardw":   strResposta = formatar_hardware(dados, strIP)
                        elif strComando == "/procs":   strResposta = formatar_processos(dados, strIP)
                        elif strComando == "/proc":    strResposta = formatar_proc(dados, pid)
                        elif strComando == "/topcpu":   strResposta = formatar_top_processos(dados, strIP, "Top 5 CPU")
                        elif strComando == "/topmem":   strResposta = formatar_top_processos(dados, strIP, "Top 5 Memória")
                        elif strComando == "/histcpu": strResposta = formatar_historico(dados, strIP)
                        
                    else: strResposta = "Agente Offline."
                else: strResposta = "Uso: `/comando [IP]`"
            else: strResposta = "?? Comando desconhecido."

            requests.post(strURLSendMessage, 
                          data={'chat_id': intIDChat, 'text': strResposta, 'parse_mode': 'Markdown'})
    except KeyboardInterrupt:

        sys.exit('\n\nEncerrando o BOT Telegram...\n')
    except Exception as erro:
        print(f'\n\nERRO: {erro}')

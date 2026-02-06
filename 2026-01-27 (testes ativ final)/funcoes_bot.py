import struct, socket, json

# --- FUNÇÃO PARA COMUNICAÇÃO COM O AGENTE (PROTOCOL RAIZ) ---
def requisitar_agente(objSocketAgente, strComando, intPID=None):
    try:
        # Envio: Letra do comando (e PID se for o caso)
        if strComando == 'P' and intPID is not None:
            bytesPacote = strComando.encode('utf-8') + struct.pack('>I', intPID)
            objSocketAgente.sendall(bytesPacote)
        else:
            objSocketAgente.sendall(strComando.encode('utf-8'))

        # Recebimento Etapa 1: Tamanho (4 bytes Big Endian)
        bytesTamanho = objSocketAgente.recv(4)
        if not bytesTamanho: return None
        intTamanho = struct.unpack('>I', bytesTamanho)[0]

        # Recebimento Etapa 2: JSON (Leitura em chunks/pedaços)
        bytesPayload = b''
        while len(bytesPayload) < intTamanho:
            bytesPayload += objSocketAgente.recv(min(intTamanho - len(bytesPayload), 4096))
        
        return json.loads(bytesPayload.decode('utf-8'))
    except:
        return None

# --- THREAD: AGUARDAR CONEXÃO DE NOVOS AGENTES ---
def thread_aguardar_agentes(dictAgentes):
    objSocketServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    objSocketServidor.bind(('0.0.0.0', 45678))
    objSocketServidor.listen(10)
    
    while True:
        objSocketAgente, addr = objSocketServidor.accept()
        strIPAgente = addr[0]
        dictAgentes[strIPAgente] = objSocketAgente
        print(f"\n[NOVO AGENTE] Online: {strIPAgente}")

# ----------------------------------------------------------------------
def startBot() -> str:
   """
      Retorna mensagem de boas vindas do bot.
   """
   return (
      "Bem-vindo ao BOT SHOW METRICS CNAT!\n\n"
      "Este é um bot para consultar métricas de performance dos dispositivos conectados.\n\n"
      "/? → Exibe mensagem de ajuda."
    )
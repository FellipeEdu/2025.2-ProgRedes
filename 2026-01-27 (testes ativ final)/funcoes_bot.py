import struct, socket, json, time
import psutil

# --- FUNÇÕES DE COMUNICAÇÃO (MOVIDAS PARA CÁ) ---

def requisitar_agente(objSocketAgente, strComando, intPID=None):
    """Gerencia a conversa via socket com o Agente."""
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
        return {"erro": "Timeout ou falha na comunicação"}

def thread_aguardar_agentes(dictAgentes):
    """Thread que fica ouvindo novos agentes conectando."""
    objSocketServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    objSocketServidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    objSocketServidor.bind(('0.0.0.0', 45678))
    objSocketServidor.listen(10)
    while True:
        objSocketAgente, addr = objSocketServidor.accept()
        strIP = addr[0]
        dictAgentes[strIP] = objSocketAgente
        print(f"Novo Agente Conectado: {strIP}")

# ----------------------------------------------------------------------
def startBot() -> str:
    """
    Retorna mensagem de boas vindas do bot.
    """
    return (
        "Bem-vindo ao BOT SHOW METRICS CNAT\n\n"
        "Este é um bot para consultar métricas de performance dos dispositivos conectados.\n\n"
        "/? → Exibe mensagem de ajuda."
        )

def mostrarAgentes(dictAgentes) -> str:
    """
    Retorna os agentes conectados.
    """
    return (
        "Agentes conectados:\n" + ("\n".join(dictAgentes.keys()) if dictAgentes else "Nenhum")
    )

# /procs: G
def comando_procs():
    lstProcessos = []
    # Usamos .info para pegar o dicionário com pid e name
    for processo in psutil.process_iter(['pid', 'name']):
        try:
            lstProcessos.append(processo.info)
        except: pass
    return lstProcessos[:10] # Limita 10 para não travar o socket
def formatar_processos(dados, ip):
    # 'dados' aqui é uma lista vinda do Agente (comando 'G')
    strSaida = f"**Processos Ativos em {ip}:**\n```\n"
    strSaida += f"{'PID':<7} | {'NOME':<15}\n"
    strSaida += "-" * 25 + "\n"
    for p in dados: # No Agente limitamos a 10
        strSaida += f"{p['pid']:<7} | {p['name'][:15]:<15}\n"
    strSaida += "```"
    return strSaida

# /proc: P
def comando_proc(dados: bytes):
    intPID = struct.unpack('>I', dados[1:5])[0]
    try:
        processo = psutil.Process(intPID)
        resposta = {
            "ok": True,
            "pid": processo.pid,
            "nome": processo.name(),
            "path": processo.exe(),
            "mem": round(processo.memory_info().rss / (1024**2), 2),
            "cpu": processo.cpu_percent(interval=0.1)
        }
        return resposta
    except psutil.NoSuchProcess:
        return {"ok": False}
def formatar_proc(dados: dict, pid):
    #strSaida = f"Detalhes PID {pid}:\n```json\n{json.dumps(dados, indent=2)}```"
    return (
        f"Detalhes PID {pid}:\n"
        f"```• Nome: {dados.get('nome')}\n"
        f"• Uso de RAM: {dados.get('mem')} MB\n"
        f"• Uso de CPU: {dados.get('cpu')} %```\n"
    )

# /topcpu: C

# /topmem: M

# /hardw: H
def formatar_hardware(dados, ip):
    return (
        f"```**Hardware: {ip}**\n\n"
        f"• **Nome PC: ** {dados.get('nome_pc')}\n"
        f"• **SO:** {dados.get('so')}\n"
        f"• **Arquitetura:** {dados.get('arch')}\n"
        f"• **CPUs:** {dados.get('cpu_cores')} cores\n"
        f"• **RAM Total:** {dados.get('mem_total')} MB```"
    )
# /histcpu: T
def formatar_historico(dados, ip):
    lstHist = dados.get("historico", [])
    if not lstHist: return "Histórico vazio ou indisponível."
    
    strSaida = f"**Histórico de CPU (60s) - {ip}**\n\n"
    for i, valor in enumerate(lstHist):
        intSegundos = i * 5
        intBarras = int(valor / 10)
        strBarra = "■" * intBarras + "□" * (10 - intBarras)
        strSaida += f"`{intSegundos:02d}s | {strBarra} {valor:>5.1f}%` \n"
    return strSaida

# --- FUNÇÃO DE COLETA (PARA O AGENTE) ---
def thread_coletar_cpu(lstHistorico):
    """
    Função que será executada em background pelo Agente.
    Ela alimenta a lista de histórico a cada 5 segundos.
    """
    while True:
        # Pega o uso de CPU (interval=1 significa que ele mede o uso durante 1 seg)
        floatUso = psutil.cpu_percent(interval=1)
        lstHistorico.append(floatUso)
        
        # Mantém apenas as últimas 12 coletas (60 segundos)
        if len(lstHistorico) > 12:
            lstHistorico.pop(0)
            
        # Como o interval do cpu_percent já levou 1s, esperamos mais 4s
        time.sleep(4)


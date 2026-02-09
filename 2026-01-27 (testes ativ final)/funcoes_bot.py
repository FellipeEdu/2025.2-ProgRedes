import struct, socket, json, time
import psutil

# --- FUNÇÕES DE COMUNICAÇÃO ---

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

def ajudaBot() -> str:
   """
      Retorna instruções de uso do bot.
   """
   return (
      "COMANDOS DISPONÍVEIS:\n"
      "/agentes → Retorna os agentes conectados.\n"
      "/procs → Retorna 10 processos em execução no dispositivo.\n"
      "/proc → Retorna dados de um processo específico.\n"
      "/topcpu → Retorna os 5 processos que mais estão consumindo CPU.\n"
      "/topmem → Retorna os 5 processos que mais estão consumindo memória RAM.\n"
      "/hardw → Retorna dados do hardware do dispositivo.\n"
      "/histcpu → Retorna os últimos 10 processos que mais consumiram CPU.\n"
      "/? → Exibe esta mensagem de ajuda."
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
def comando_proc(dados):
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
        f"• Path: {dados.get('path')}\n"
        f"• Uso de RAM: {dados.get('mem')} MB\n"
        f"• Uso de CPU: {dados.get('cpu')} %```\n"
    )

# /topcpu: C
# /topmem: M
def comando_topcpu():
    lstProcessos = []
    for processo in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            lstProcessos.append(processo.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Ordena do maior para o menor e pega os 5 primeiros
    return sorted(lstProcessos, key=lambda x: x['cpu_percent'], reverse=True)[:5]
def comando_topmem():
    lstProcessos = []
    for processo in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            # Pegamos o RSS e convertemos para MB logo aqui
            p_info = processo.info
            p_info['mem_mb'] = round(processo.info['memory_info'].rss / (1024**2), 2)
            lstProcessos.append(p_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Ordena pelo campo mem_mb que criamos
    return sorted(lstProcessos, key=lambda x: x['mem_mb'], reverse=True)[:5]
# ----------------------------------------------------------------------
def formatar_top_processos(dados, ip, titulo):
    """Formata a lista de processos em uma tabela Markdown."""
    strSaida = f"**{titulo} - {ip}**\n"
    strSaida += "```\n"
    strSaida += f"{'PID':<7} | {'NOME':<15}\n"
    strSaida += "-" * 30 + "\n"
    
    for processo in dados:
        # Verifica se o dado é de CPU ou Memória para exibir a unidade certa
        valor = f"{processo['cpu_percent']}%" if 'cpu_percent' in processo else f"{processo['mem_mb']}MB"
        strSaida += f"{processo['pid']:<7} | {processo['name'][:15]:<15}\n"
    
    strSaida += "```"
    return strSaida

# /hardw: H
def formatar_hardware(dados, ip):
    return (
        f"```Hardware: {ip}\n\n"
        f"• Nome PC: {dados.get('nome_pc')}\n"
        f"• SO: {dados.get('so')}\n"
        f"• Arquitetura: {dados.get('arch')}\n"
        f"• CPUs: {dados.get('cpu_cores')} cores\n"
        f"• RAM Total: {dados.get('mem_total')} MB```"
    )
# /histcpu: T
def thread_coletar_cpu(lstHistorico):
    """
    Função que será executada em background pelo Agente.
    Ela alimenta a lista de histórico a cada 5 segundos.
    """
    while True:
        # Pega o uso global de CPU
        floatUso = psutil.cpu_percent(interval=1)
        
        # Busca o processo com maior consumo no momento
        strTopProc = "Sistema"
        floatMax = -1.0
        
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                # O psutil já terá o cálculo do intervalo de 1s acima
                if proc.info['cpu_percent'] > floatMax:
                    floatMax = proc.info['cpu_percent']
                    strTopProc = proc.info['name']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Agora guardamos um dicionário com os dois dados
        lstHistorico.append({"cpu": floatUso, "proc": strTopProc})
        
        if len(lstHistorico) > 12:
            lstHistorico.pop(0)
            
        time.sleep(4)
def formatar_historico(dados, ip):
    lstHist = dados.get("historico", [])
    if not lstHist: return "Histórico vazio ou indisponível."
    
    strSaida = f"Histórico de CPU (60s) - {ip}**\n\n"
    strSaida += "```\n"
    strSaida += f"{'TEMPO':<7} | {'NOME':<20} | {'VALOR'}\n"
    for i, valor in enumerate(lstHist):
        intSegundos = i * 5

        strTempo = f"{intSegundos}s"
        floatCPU = valor.get("cpu", 0.0)
        strProc  = valor.get("proc", "N/A")

        strSaida += f"{strTempo:<7} | {strProc:20} | {floatCPU:>5.1f}%\n"
    strSaida += "```"
    return strSaida
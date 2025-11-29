import requests, os, zipfile, struct
from datetime import datetime

dirQuestao = os.path.dirname(__file__)

# auxiliar

def criarArquivoDir(diretorio_relativo):
    caminho_Completo_Dir = os.path.join(dirQuestao, diretorio_relativo)
    try:
        os.makedirs(caminho_Completo_Dir, exist_ok=True) 
        # print(f"\nDiretório {diretorio_relativo} garantido com sucesso.") # Opcional
    except OSError as erro:
        print(f"\n! Erro fatal ao garantir o diretório {diretorio_relativo}: {erro}")
        raise

# Download e Descompactação

def baixar_arquivo_pcap(url):
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Extrai o nome do arquivo da URL (última parte)
        nome_arquivo = url.split('/')[-1]
        caminho_Completo = os.path.join(dirQuestao, nome_arquivo)

        # Salva o conteúdo do arquivo
        with open(caminho_Completo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nDownload concluído: {caminho_Completo}")
        return caminho_Completo
        
    except requests.exceptions.RequestException as erro:
        print(f"\n! Erro de requisição ao baixar o arquivo: {erro}")
        return None

def descompactar_arquivo(caminho_zip):
    # 1. Obter o nome base do arquivo (sem o caminho)
    nome_Base_Zip = os.path.basename(caminho_zip).replace('.zip', '')
    
    # --- Tenta Extrair a Data (AAAAMMDD) da String ---
    # Substitui todos os caracteres não-dígitos por um separador único (e.g., espaço)
    # E foca no formato YYYY-MM-DD (2025-10-08)
    
    # Itera sobre os caracteres para isolar a data (substituindo o uso de 're')
    
    #data_candidata = ""
    # Se o nome do arquivo for 2025-10-08-traffic-..., a data está no início.
    if nome_Base_Zip.startswith(('20', '19')): # Assumindo anos no formato 20xx ou 19xx
        
        # Pega os primeiros 10 caracteres (YYYY-MM-DD)
        segmento = nome_Base_Zip[:10]
        
        if len(segmento) == 10 and segmento[4] == '-' and segmento[7] == '-':
            # Formato YYYY-MM-DD encontrado! Converte para AAAAMMDD
            data_do_nome = segmento.replace('-', '')
            
    # --- Continuação da Lógica ---
    
    if data_do_nome and data_do_nome.isdigit() and len(data_do_nome) == 8:
        senha_base = f"infected_{data_do_nome}"
    else:
        # FALLBACK: Se a data não foi encontrada ou é inválida, usa a data de modificação do arquivo
        timestamp = os.path.getmtime(caminho_zip)
        data = datetime.fromtimestamp(timestamp)
        senha_base = f"infected_{data.strftime('%Y%m%d')}"
        print(f"Aviso: Data não encontrada no nome. Usando data de modificação: {senha_base}")
    
    try:
        senha = senha_base.encode('utf-8')

        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            zip_ref.extractall(path=dirQuestao, pwd=senha)
        
        # O arquivo .pcap deve ter o mesmo nome do .zip (sem a extensão .zip)
        nome_pcap = os.path.basename(caminho_zip).replace('.zip', '')
        caminho_pcap = os.path.join(dirQuestao, nome_pcap)
        
        print(f"Descompactação concluída. Arquivo .pcap: {caminho_pcap}")
        return caminho_pcap
        
    except zipfile.BadZipFile:
        print("\n! Erro: Arquivo ZIP inválido ou corrompido.")
    except Exception as erro:
        print(f"\n! Erro na descompactação (Senha incorreta ou data inválida): {erro} !")
        # Uma mensagem de erro mais útil ao usuário pode ser:
        print(f"A senha esperada era algo como: {senha_base}")
    return None

# Análise PCAP (Usando STRUCT)

# --- Constantes do PCAP (Pode estar no topo do arquivo funcoes.py) ---
PACKET_HEADER_FORMAT = '<IIII'
PACKET_HEADER_SIZE = 16
GLOBAL_HEADER_SIZE = 24

# Este formato é para ler os 24 bytes do Cabeçalho Global do PCAP
# I = magic (4 bytes), H = major (2 bytes), H = minor (2 bytes)
# I = thiszone (4 bytes), I = sigfigs (4 bytes)
# I = snaplen (4 bytes), I = linktype (4 bytes)
GLOBAL_HEADER_STRUCT_FORMAT = '<I H H I I I I'

def analisar_pcap(caminho_pcap):
    resultados = {
        'inicio_captura': 0,
        'fim_captura': 0,
        'maior_tamanho_tcp': 0,
        'pacotes_cortados': 0,
        'tamanho_total_udp': 0,
        'contagem_udp': 0,
        'trafego_ip': {}, # Armazena (IP_A, IP_B): bytes
        'ips_interface': set(),
        'contagem_ip': set()
    }

    # Dicionário de Mapeamento Link Type para Tamanho do Cabeçalho de Enlace (Link-Layer)
    LINK_TYPE_MAP = {
        1: 14,   # Ethernet (padrão)
        0: 4,    # BSD Loopback
        101: 4   # Loopback
    }

    # Valor padrão que será corrigido após a leitura do Cabeçalho Global
    IP_START_OFFSET = 14
    
    try:
        with open(caminho_pcap, 'rb') as arquivo:
            # 1. LER e DESEMPACOTAR o Cabeçalho Global (24 bytes)
            global_header_bytes = arquivo.read(GLOBAL_HEADER_SIZE)
            if len(global_header_bytes) < GLOBAL_HEADER_SIZE:
                print("Arquivo PCAP muito pequeno para ser válido.")
                return resultados
            
            # Desempacota os 7 campos. O último campo (linktype) é o que importa
            _, _, _, _, _, _, linktype = struct.unpack(GLOBAL_HEADER_STRUCT_FORMAT, global_header_bytes)
            
            # definindo o IP_START_OFFSET correto
            IP_START_OFFSET = LINK_TYPE_MAP.get(linktype, 14) 
            print(f"Link Type detectado: {linktype}. Cabeçalho de Enlace: {IP_START_OFFSET} bytes.")

            # Ponteiro 'arquivo' está posicionado no primeiro Packet Header (PH)
            
            while True:
                # tenta ler o PH
                packet_header_bytes = arquivo.read(PACKET_HEADER_SIZE)
                if len(packet_header_bytes) < PACKET_HEADER_SIZE:
                    break 
                
                # desempacota o PH
                ts, ts_usec, captured_len, orig_len = struct.unpack(PACKET_HEADER_FORMAT, packet_header_bytes)
                
                # processa o tempo (timestamp) 
                timestamp_s = ts + (ts_usec / 1000000.0)
                if resultados['inicio_captura'] == 0:
                    resultados['inicio_captura'] = timestamp_s
                resultados['fim_captura'] = timestamp_s
                
                # verifica pacotes cortados (Snaps Len)
                if captured_len < orig_len:
                    resultados['pacotes_cortados'] += 1

                # lê os dados do pacote (captured_len = tamanho real salvo)
                packet_Dados = arquivo.read(captured_len)
                if len(packet_Dados) < captured_len:
                    break
                    
                # analisando cabeçalho IP (IP_START_OFFSET bytes depois)
                if captured_len >= IP_START_OFFSET + 20: # 14 bytes Ethernet + 20 bytes IP mínimo
                    ip_Header_Data = packet_Dados[IP_START_OFFSET : IP_START_OFFSET + 20]
                    
                    # Formato IP: B (Versão/IHL), B (TOS), H (Total Length), etc.
                    # Pegamos: Versão/IHL (1 byte), Protocolo (1 byte no offset 9),
                    #          Source IP (4 bytes no offset 12), Dest IP (4 bytes no offset 16)
                    # Formato struct: ! B x B x x x x x x 4s 4s
                    # O '!' (network/big-endian) é crucial para IP/TCP
                    
                    # Extrai campos importantes: Total Length (offset 2), Protocol (offset 9), Source IP (offset 12), Dest IP (offset 16)
                    # ! B B H H B B B B 4s 4s
                    #   0 1 2 4 6 8 9 10 12 16
                    IP_HEADER_FORMAT_FULL = '!BBHHHBBH4s4s'

                    ip_Header_Data = packet_Dados[IP_START_OFFSET : IP_START_OFFSET + 20]

                    # Desempacota o cabeçalho IP de 20 bytes
                    ip_Campos_Completo = struct.unpack(IP_HEADER_FORMAT_FULL, ip_Header_Data)
                    
                    ihl_Versao = ip_Campos_Completo[0]
                    ip_Header_Tam = (ihl_Versao & 0xF) * 4
                    #ip_total_length = ip_Campos_Completo[2]
                    protocolo = ip_Campos_Completo[6] 
                    source_IP_Bruto = ip_Campos_Completo[8]
                    dest_IP_bruto = ip_Campos_Completo[9]
                    
                    # converte IPs binários para formato legível
                    source_ip = '.'.join(map(str, source_IP_Bruto))
                    dest_ip = '.'.join(map(str, dest_IP_bruto))
                    
                    # registra IP
                    resultados['contagem_ip'].add(source_ip)
                    resultados['contagem_ip'].add(dest_ip)
                    
                    # contabiliza Tráfego de IP (Par de IP)
                    # garante ordem canônica para o par (a, b) ou (b, a)
                    ip_pair = tuple(sorted((source_ip, dest_ip)))
                    resultados['trafego_ip'][ip_pair] = resultados['trafego_ip'].get(ip_pair, 0) + captured_len
                    
                    # --- Análise TCP/UDP ---
                    
                    # Posição do cabeçalho TCP/UDP (após o Cabeçalho Ethernet + IP)
                    TRANSPORT_START = IP_START_OFFSET + ip_Header_Tam

                    if protocolo == 6:  # TCP
                        # Tamanho real do pacote TCP é o incl_len menos os headers
                        tcp_packet_size = captured_len
                        if tcp_packet_size > resultados['maior_tamanho_tcp']:
                            resultados['maior_tamanho_tcp'] = tcp_packet_size

                    elif protocolo == 17: # UDP
                        resultados['tamanho_total_udp'] += captured_len
                        resultados['contagem_udp'] += 1
                        
                # 8. Atualiza IPs da Interface (Simulação: assumindo que o IP mais comum é o da interface)
                # Esta é uma simplificação para responder à questão:
                # O IP de origem do primeiro pacote é frequentemente o da interface.
                # Para uma análise real, precisaríamos de mais contexto, mas para o exercício
                # podemos assumir uma heurística:
                if 'ip_interface_base' not in resultados:
                    if ip_Header_Data:
                        resultados['ip_interface_base'] = source_ip

    except IOError as erro:
        print(f"\n! Erro de I/O ao ler o arquivo .pcap: {erro} !")
    except Exception as erro:
        print(f"\n! Erro geral durante a análise: {erro} !")

    # 9. Realiza formatação e calculos finais
    
    # Calcular IP com maior tráfego
    if resultados['trafego_ip']:
        maior_par_ip = max(resultados['trafego_ip'], key=resultados['trafego_ip'].get)
        resultados['maior_trafego_ip'] = (maior_par_ip, resultados['trafego_ip'][maior_par_ip])
    
    # Calcular Tamanho Médio UDP
    if resultados['contagem_udp'] > 0:
        resultados['tamanho_medio_udp'] = resultados['tamanho_total_udp'] / resultados['contagem_udp']
    else:
        resultados['tamanho_medio_udp'] = 0
        
    # Calcular Interações da Interface (IPs que não são o IP base)
    if 'ip_interface_base' in resultados:
        ip_base = resultados['ip_interface_base']
        # IPs que interagiram com o IP base
        for ip_par, _ in resultados['trafego_ip'].items():
            if ip_base in ip_par:
                # Adiciona o IP que não é o IP base
                other_ip = ip_par[0] if ip_par[1] == ip_base else ip_par[1]
                resultados['ips_interface'].add(other_ip)
        
    return resultados

# Exibição

def exibir_resultados(dados):
    print(f"\n{"="*50}\nRESULTADOS DA ANÁLISE PCAP (STRUCT)\n{"="*50}")

    if dados['inicio_captura'] > 0:
        print(f"Início da Captura: {datetime.fromtimestamp(dados['inicio_captura']).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"Término da Captura: {datetime.fromtimestamp(dados['fim_captura']).strftime('%Y-%m-%d %H:%M:%S.%f')}")
    else:
        print("Não foram encontrados pacotes válidos.")

    print("\n#------- Estatísticas de Pacotes -------#")
    
    print(f"- Maior Tamanho de Pacote TCP Capturado: {dados['maior_tamanho_tcp']} bytes")

    print(f"- Pacotes que NÃO foram salvos na totalidade (cortados): {dados['pacotes_cortados']}")
    
    print(f"- Tamanho Médio dos Pacotes UDP: {dados['tamanho_medio_udp']:.2f} bytes")

    if 'maior_trafego_ip' in dados:
        ip_Par, traffic = dados['maior_trafego_ip']
        print(f"- Par de IPs com Maior Tráfego: {ip_Par[0]} <-> {ip_Par[1]} ({traffic} bytes)")
    
    # Interações do IP da Interface
    if 'ip_interface_base' in dados:
        print(f"\n- IP da Interface (assumido): {dados['ip_interface_base']}")
        print(f"- Interagiu com {len(dados['ips_interface'])} outros IPs.")
        print(f"- IPs Interagidos: {dados['ips_interface']}")
    else:
        print("\n! Não foi possível determinar o IP da interface.")

    print("="*50)

    # Campos dos Headers IP (Exibição simplificada)
    print("\n--- Conteúdo do Cabeçalho IP (Exemplo) ---")
    print("O módulo STRUCT permite extrair campos como:")
    print("  - Versão/IHL (Internet Header Length)")
    print("  - Comprimento Total do Pacote (Total Length)")
    print("  - Protocolo (ex: 6=TCP, 17=UDP)")
    print("  - Endereço IP de Origem/Destino (Source/Dest IP)")
    print("Para exibir o conteúdo de CADA campo, seria necessário desempacotar o cabeçalho IP completo (20 bytes),\n" \
    "mas o código extraiu os campos principais para a análise.")
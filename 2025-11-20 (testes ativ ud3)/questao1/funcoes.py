import sys, os, requests, json

dirQuestao = os.path.dirname(__file__)

def criarArquivos(diretorio):
    #Cria um diretório no caminho especificado se ele ainda não existir.
    try:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
            print(f"Diretório criado: {diretorio}")
        else:
            print(f"Diretório já existe: {diretorio}")
    except OSError as erro:
        print(f"Erro ao criar o diretório {diretorio}: {erro}")
        raise

def nomeArqHost(url):
    # Extrai o host da URL e o formata para ser o nome base do arquivo,
    # substituindo pontos por hífens.

    # remove o prefixo https
    if url.startswith('https://'):
        host_Original = url[8:]
    elif url.startswith('http://'):
        host_Original = url[7:]
    else:
        host_Original = url
    
    # pega apenas a parte antes do primeiro '/'
    if '/' in host_Original:
        host_Original = host_Original.split('/')[0]
        
    # remove porta se existir
    if ':' in host_Original:
        host_Original = host_Original.split(':')[0]
        
    # substitui os pontos por hifens para formar o nome base do arquivo
    nome_Original_Arq = host_Original.replace('.', '-')
    
    # retorna o nome limpo
    return nome_Original_Arq

def trocaCharNome(nome):
    caracteresInvalidos = ['%', '#', '?', '&', '=', '+', ':', ';', '$', '@', '[', ']', '(', ')', '{', '}', '!', '`', '~', '^', '*', '"', "'"]
    
    nomeNovo = nome
    for char in caracteresInvalidos:
        nomeNovo = nomeNovo.replace(char, '_')
        
    return nomeNovo

# --- Funções de Download e Salvamento ---

def baixar_e_salvar_header(url):
    """
    Faz a requisição, baixa o HEADER e salva em formato JSON na pasta 'headers'.
    """
    DIRETORIO_HEADERS = "headers"
    
    try:
        # 1. Cria a pasta 'headers'
        criarArquivos(DIRETORIO_HEADERS)
        
        # 2. Faz a requisição
        response = requests.get(url, allow_redirects=True, timeout=10)
        response.raise_for_status() # Lança exceção para códigos de status 4xx/5xx

        # 3. Formata o nome do arquivo
        nome_base = nomeArqHost(url)
        # O nome do arquivo header não deve conter caracteres especiais além do '-' gerado
        nome_arquivo = f"{trocaCharNome(nome_base)}.json" 
        caminho_completo = os.path.join(DIRETORIO_HEADERS, nome_arquivo)
        
        # 4. Converte o header para JSON e salva
        header_json = json.dumps(dict(response.headers), indent=4)
        
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(header_json)
        
        print(f"Header salvo com sucesso em: {caminho_completo}")
        return response # Retorna a resposta para uso no salvamento do conteúdo
    
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao baixar o header para {url}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição (conexão/timeout) para {url}: {e}")
    except Exception as e:
        print(f"Erro inesperado ao processar o header: {e}")
        
    return None

def salvar_conteudo(response, url):
    """
    Salva o conteúdo da resposta baseado no Content-Type do header.
    """
    if response is None:
        return
        
    content_type = response.headers.get('Content-Type', 'application/octet-stream').lower()
    
    if 'text/html' in content_type:
        tipo = 'html'
        extensao = '.html'
        diretorio = 'content_html'
        
        # Nome do arquivo: base no host
        nome_base = nomeArqHost(url)
        nome_arquivo = nome_base + extensao

    elif 'image/jpeg' in content_type:
        tipo = 'jpeg'
        extensao = '.jpg'
        diretorio = 'content_jpg'
        
        # Nome do arquivo: última parte da URL (simulação de urlparse.path.split)
        # 1. Remove o host para pegar o caminho
        caminho_url = url.split(nomeArqHost(url).replace('-', '.'))[1]
        
        # 2. Pega a última parte do caminho
        partes = caminho_url.split('/')
        nome_base_bruto = partes[-1] if partes[-1] else "image"
        
        # Se a URL não termina em .jpg, garante a extensão
        if not nome_base_bruto.lower().endswith(extensao):
             nome_base_bruto += extensao
             
        nome_arquivo = nome_base_bruto

    else:
        # Padrão para outros tipos de arquivo
        tipo = 'outro'
        # Tenta inferir extensão
        if '/' in content_type:
            extensao = f".{content_type.split('/')[-1].split(';')[0]}"
        else:
            extensao = ".bin"
            
        diretorio = 'content_outros'

        # Nome do arquivo: base no host + extensão
        nome_base = nomeArqHost(url)
        nome_arquivo = nome_base + extensao
        
        print(f"Conteúdo de tipo não mapeado ({content_type}) salvo como {tipo}.")

    try:
        # 1. Limpa o nome do arquivo de caracteres especiais
        nome_arquivo_limpo = trocaCharNome(nome_arquivo)
        
        # 2. Cria o diretório de conteúdo
        criarArquivos(diretorio)
        
        # 3. Define o caminho completo
        caminho_completo = os.path.join(diretorio, nome_arquivo_limpo)
        
        # 4. Salva o conteúdo em modo binário
        with open(caminho_completo, 'wb') as f:
            f.write(response.content)
            
        print(f"Conteúdo ({tipo}) salvo com sucesso em: {caminho_completo}")

    except Exception as e:
        print(f"Erro ao salvar o conteúdo: {e}")
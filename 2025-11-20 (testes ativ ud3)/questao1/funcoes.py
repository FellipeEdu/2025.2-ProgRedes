import os, requests, json

dirQuestao = os.path.dirname(__file__)

def criarArquivoDir(diretorio):
    caminho_Absoluto = os.path.join(dirQuestao, diretorio)

    try:
        if not os.path.exists(diretorio):
            os.makedirs(caminho_Absoluto, exist_ok=True)
            print(f"\nDiretório criado: {diretorio}")
        else:
            print(f"\nDiretório já existe: {diretorio}")
    except OSError as erro:
        print(f"\nErro ao criar o diretório {diretorio}: {erro}")
        raise

def nomeArqHost(url):

    if url.startswith('https://'):
        host_Original = url[8:]
    elif url.startswith('http://'):
        host_Original = url[7:]
    else:
        host_Original = url
    
    if '/' in host_Original:
        host_Original = host_Original.split('/')[0]
        
    if ':' in host_Original:
        host_Original = host_Original.split(':')[0]
        
    nome_Original_Arq = host_Original.replace('.', '-')
    
    return nome_Original_Arq

def limpaNomeArq(nome):
    caracteres_Invalidos = ['%', '#', '?', '&', '=', '+', ':', ';', '$', '@', '[', ']', '(', ')', '{', '}', '!', '`', '~', '^', '*', '"', "'"]
    
    nome_Novo = nome
    for char in caracteres_Invalidos:
        nome_Novo = nome_Novo.replace(char, '_')
        
    return nome_Novo


def salvarHeader(url):
    
    DIRETORIO_HEADERS = "headers"
    
    try:
        # cria a pasta 'headers'
        criarArquivoDir(DIRETORIO_HEADERS)

        response = requests.get(url)
        response.raise_for_status()

        # formata o nome do arquivo
        nome_Base = nomeArqHost(url)
        nome_Arquivo = f"{limpaNomeArq(nome_Base)}.json" 
        caminho_Completo = os.path.join(dirQuestao, DIRETORIO_HEADERS, nome_Arquivo)
        
        # converte o header para JSON e salva
        header = json.dumps(dict(response.headers), indent=4)
        
        with open(caminho_Completo, 'w', encoding='utf-8') as arquivo:
            arquivo.write(header)
        
        print(f"\nConteúdo do Cabeçalho:\n{response.headers}\n")

        print(f"Header salvo com sucesso em: {caminho_Completo}")
        return response
    
    except requests.exceptions.HTTPError as erro:
        print(f"\nErro HTTP ao baixar o header para {url}: {erro}")
    except requests.exceptions.RequestException as erro:
        print(f"\nErro de requisição (conexão/timeout) para {url}: {erro}")
    except Exception as erro:
        print(f"\nErro inesperado ao processar o header: {erro}")
        
    return None

def salvarConteudo(response, url):
    
    if response is None: return
        
    content_Type = response.headers.get('Content-Type', '').lower()
    
    if 'text/html' in content_Type:
        tipo = 'html'
        extensao = '.html'
        diretorio = 'content_html'
        
        # Nome do arquivo: base no host
        nome_Base = nomeArqHost(url)
        nome_Arq = nome_Base + extensao

    elif 'image/jpeg' in content_Type:
        tipo = 'jpeg'
        extensao = '.jpg'
        diretorio = 'content_jpg'
        
        # remove o host para pegar o caminho
        caminho_url = url.split(nomeArqHost(url).replace('-', '.'))[1]
        
        # pega a última parte do caminho
        partes = caminho_url.split('/')
        nome_Base_Completo = partes[-1] if partes[-1] else "image"
        
        # garante a extensão se a URL não termina em .jpg
        if not nome_Base_Completo.lower().endswith(extensao):
             nome_Base_Completo += extensao
             
        nome_Arq = nome_Base_Completo

    else:
        # para outros tipos de arquivo tenta adivinhar a extensão
        tipo = 'outro'

        if '/' in content_Type:
            extensao = f".{content_Type.split('/')[-1].split(';')[0]}"
        else:
            extensao = ".bin"
            
        diretorio = 'content_outros'

        nome_Base = nomeArqHost(url)
        nome_Arq = nome_Base + extensao
        
        print(f"Conteúdo de tipo não mapeado ({content_Type}) salvo como {tipo}.")

    try:
        nome_Arq_Limpo = limpaNomeArq(nome_Arq)
        
        criarArquivoDir(diretorio)
        
        caminho_Completo = os.path.join(dirQuestao, diretorio, nome_Arq_Limpo)
        
        with open(caminho_Completo, 'wb') as f:
            f.write(response.content)
            
        print(f"\nConteúdo ({tipo}) salvo com sucesso em: {caminho_Completo}")

    except Exception as erro:
        print(f"Erro ao salvar o conteúdo: {erro}")
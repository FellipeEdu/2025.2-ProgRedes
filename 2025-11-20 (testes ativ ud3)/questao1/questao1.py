import sys; from funcoes import *  

print("--- Download de Arquivos de Rede (Python/requests) ---")
    
while True:
    url = input("\nPor favor, informe a URL para download (ou 'sair' para encerrar): ").strip()
        
    if url.lower() == 'sair':
        print("Encerrando o programa. Até mais!")
        break
            
    if not url:
        print("A URL não pode estar vazia.")
        continue
            
    # Garante que a URL comece com http(s):// para o requests
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
            
    print(f"{'*' * 30}\nIniciando processamento da URL: {url}")
        
    # baixa e salva HEADER
    # A função já trata as exceções de requisição e retorna o objeto 'response'
    response = salvarHeader(url)

    # 2. Salvar o CONTEÚDO se a requisição do header foi bem-sucedida
    if response is not None:
        salvarConteudo(response, url)
        
    print("\nProcessamento da URL concluído.")

    '''try:

    except requests.exceptions.ConnectTimeout:
        sys.exit(f'\nERRO: A conexão demorou demais (Timeout). O servidor pode estar offline ou lento...\n')
    except requests.exceptions.RequestException as erro:
        sys.exit(f'\nERRO: Ocorreu um erro ao fazer a requisição: {erro}\n')
    except Exception as erro:
        sys.exit(f'\nERRO: {erro}\n')'''
from funcoes import *  

print("----- Download de Arquivos de Rede -----")
    
while True:
    url = input("\nPor favor, informe a URL para download (ou 'sair' para encerrar): ").strip()
        
    if url.lower() == 'sair': break
            
    if not url:
        print("A URL não pode estar vazia.")
        continue
            
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
            
    print(f"{'*' * 50}\nIniciando processamento da URL: {url}")
        
    # baixa e salva header
    response = salvarHeader(url)

    # salvando conteudo
    if response is not None:
        salvarConteudo(response, url)
        
    print(f"\nProcessamento da URL concluído.\n{'*' * 50}")

print("Encerrando o programa.")
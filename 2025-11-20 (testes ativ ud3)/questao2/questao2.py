from funcoes import *

print("------ Análise de Arquivos PCAP (struct) ------")
    
while True:
    url_Zip = input("\nInforme a URL do arquivo .pcap.zip (ou 'sair'): ").strip()
    
    if url_Zip.lower() == 'sair': break
            
    if not url_Zip:
        print("URL não pode estar vazia.")
        continue
            
    # 1. Download do Arquivo
    try:
        caminho_Zip = baixar_arquivo_pcap(url_Zip)
        if caminho_Zip is None:
            continue
                
        # 2. Descompactação
        caminho_Pcap = descompactar_arquivo(caminho_Zip)
        if caminho_Pcap is None:
            continue
            
        # 3. Análise do PCAP
        print("\nIniciando análise do arquivo .pcap. Isso pode levar alguns segundos...")
        resultados = analisar_pcap(caminho_Pcap)
            
        # 4. Exibição dos Resultados
        exibir_resultados(resultados)
            
    except Exception as erro:
        print(f"\n! Ocorreu um erro inesperado durante o processo completo: {erro} !")
            
    print(f"\nProcessamento concluído.\n{"*" * 70}")

print("Encerrando o programa.")
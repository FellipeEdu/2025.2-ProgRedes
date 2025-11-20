import requests, sys, os

strDirAtual = os.path.dirname(__file__)

while True:
    #strURL = input('Digite uma URL para analisar, ou nada para finalizar o programa: ')
    #if not strURL: break 

    #dicHeaders = { 'User-Agent': 'MeuAppPython/1.0' }

    try:

    except requests.exceptions.ConnectTimeout:
        sys.exit(f'\nERRO: A conexão demorou demais (Timeout). O servidor pode estar offline ou lento...\n')
    except requests.exceptions.RequestException as erro:
        sys.exit(f'\nERRO: Ocorreu um erro ao fazer a requisição: {erro}\n')
    except Exception as erro:
        sys.exit(f'\nERRO: {erro}\n')
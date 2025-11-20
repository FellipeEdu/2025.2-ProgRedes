import requests, sys, os

dirQuestao = os.path.dirname(__file__)

def criarArquivos(diretorio):
    """
    Cria um diretório no caminho especificado se ele ainda não existir.
    """
    try:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
            print(f"Diretório criado: {diretorio}")
        else:
            print(f"Diretório já existe: {diretorio}")
    except OSError as e:
        # Lidar com erros de permissão ou outros erros de criação
        print(f"Erro ao criar o diretório {diretorio}: {e}")
        raise # Re-lança para ser capturado pelo chamador, se necessário
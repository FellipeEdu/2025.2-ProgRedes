import os

diretorio = os.path.dirname(__file__)

def inicializaRAID():
    quantDiscos = int(input('Quantidade de discos: '))
    tamanhoDiscos = int(input('Tamanho de cada disco (em bytes): '))
    tamanhoBlocos = int(input('Tamanho de blocos dos discos (em bytes): '))

    for disco in range(quantDiscos):
        open(f'{diretorio}\\disco{disco}', '+ab')
    
def obtemRAID()
    
def escreveRAID()
    
def leRAID()
    
def removeDiscoRAID()
    
def constroiDiscoRAID()
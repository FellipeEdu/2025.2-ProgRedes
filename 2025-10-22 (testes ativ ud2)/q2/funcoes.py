import os

def inicializaRAID():
    quantDiscos = int(input('Quantidade de discos: '))
    tamanhoDiscos = int(input('Tamanho de cada disco (em bytes): '))
    tamanhoBlocos = int(input('Tamanho de blocos dos discos (em bytes): '))
    pasta = input('Nome da pasta dos arquivos: ')

    diretorio = os.makedirs(pasta, exist_ok=True)

    for disco in range(quantDiscos - 1):
        open(f'{diretorio}\\disco{disco}.bin', '+ab')


    
def obtemRAID()
    
def escreveRAID()
    
def leRAID()
    
def removeDiscoRAID()
    
def constroiDiscoRAID()
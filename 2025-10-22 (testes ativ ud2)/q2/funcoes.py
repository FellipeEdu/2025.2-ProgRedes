import os

RAID_CONFIG = {
    'quantDiscos': 0,        # N total de discos (Dados + Paridade)
    'tamanhoDiscos': 0,      # Tamanho em bytes de CADA arquivo .bin
    'tamanhoBlocos': 0,      # Tamanho do bloco em bytes
    'diretorio': '',         # Pasta onde os arquivos estão
    'indiceParidade': 0,     # Índice do disco de paridade (N-1)
    'quantDiscosDados': 0    # N de discos de dados (N-1)
}

def getConfig():
    return RAID_CONFIG

# Mantenho as versões anteriores, pois elas funcionam perfeitamente sem 'struct'
# e sem precisar de um formato fixo (como 'i' para 4 bytes).
def intParaBytes(valor, tamanho):
    return valor.to_bytes(tamanho, byteorder='little')

def bytesParaInt(dados):
    return int.from_bytes(dados, byteorder='little')

def calcularXorBytes(listaBlocos):
    if not listaBlocos:
        return b''
    
    paridade = bytearray(listaBlocos[0])
    
    for bloco in listaBlocos[1:]:
        if len(paridade) != len(bloco):
             raise ValueError("Blocos com tamanhos diferentes!")
             
        for i in range(len(paridade)):
            paridade[i] ^= bloco[i]
        
    return bytes(paridade)

def posicaoLogica(posicaoByte, tamBloco, quantDados):
    """
    Calcula a localização física (disco e posição absoluta no arquivo)
    a partir da posição lógica (do RAID).
    """
    numBloco = posicaoByte // tamBloco
    discoDadosX = numBloco % quantDados
    bloco_no_disco = numBloco // quantDados
    offset_no_bloco = posicaoByte % tamBloco
    posFisica = (bloco_no_disco * tamBloco) + offset_no_bloco

    return discoDadosX, posFisica

def inicializaRAID():
    print("\n--- 1. INICIALIZAR RAID ---")
    
    try:
        quantDiscos = int(input('Quantidade de discos (N > 1): '))
        if quantDiscos <= 1:
            print("O RAID requer no mínimo 2 discos.")
            return

        tamanhoDiscos = int(input('Tamanho de cada disco (em bytes): '))
        if tamanhoDiscos <= 0:
            print("O tamanho do disco deve ser positivo.")
            return

        tamanhoBlocos = int(input('Tamanho de blocos dos discos (em bytes): '))
        if tamanhoBlocos <= 0 or tamanhoDiscos % tamanhoBlocos != 0:
             print("Tamanho de bloco inválido ou não divisor do tamanho do disco.")
             return
             
        diretorio = input('Informe o diretório onde os arquivos serão criados: ')

    except ValueError:
        print("Entrada inválida. Tente novamente.")
        return

    # salva configuração
    RAID_CONFIG['quantDiscos'] = quantDiscos
    RAID_CONFIG['tamanhoDiscos'] = tamanhoDiscos
    RAID_CONFIG['tamanhoBlocos'] = tamanhoBlocos
    RAID_CONFIG['diretorio'] = diretorio
    RAID_CONFIG['indiceParidade'] = quantDiscos - 1
    RAID_CONFIG['quantDiscosDados'] = quantDiscos - 1
    
    os.makedirs(diretorio, exist_ok=True)
    
    blocoVazio = b'\x00' * tamanhoBlocos
    numBlocos = tamanhoDiscos // tamanhoBlocos
    
    for disco in range(quantDiscos):
        caminhoArquivo = os.path.join(diretorio, f'disco{disco}.bin')
        
        with open(caminhoArquivo, 'ab+') as arquivo:
            arquivo.seek(0)
            arquivo.truncate(0)
            arquivo.seek(0) 

            print(f"Criando e zerando disco{disco}.bin...")
            for _ in range(numBlocos):
                arquivo.write(blocoVazio)
            
        tamanhoReal = os.path.getsize(caminhoArquivo)
        if tamanhoReal != tamanhoDiscos:
            print(f"AVISO: {tamanhoReal} bytes, esperado {tamanhoDiscos} bytes.")
        else:
            print(f"Sucesso: disco{disco}.bin criado.")

    print("\nInicialização RAID concluída!")

def obtemRAID():
    print("\n--- 2. OBTER RAID EXISTENTE ---")
    
    try:
        quantDiscos = int(input('Quantidade de discos: '))
        tamanhoDiscos = int(input('Tamanho dos discos (bytes): '))
        tamanhoBlocos = int(input('Tamanho dos blocos (bytes): '))
        diretorio = input('Diretório: ')
        
        # Verificações de existência
        configValida = True
        for disco in range(quantDiscos):
             caminho = os.path.join(diretorio, f'disco{disco}.bin')
             if not os.path.exists(caminho) or os.path.getsize(caminho) != tamanhoDiscos:
                 print(f"Erro: Arquivo {caminho} não encontrado ou tamanho incorreto.")
                 configValida = False
                 break
        
        if configValida:
            # salvando configuração
            RAID_CONFIG['quantDiscos'] = quantDiscos
            RAID_CONFIG['tamanhoDiscos'] = tamanhoDiscos
            RAID_CONFIG['tamanhoBlocos'] = tamanhoBlocos
            RAID_CONFIG['diretorio'] = diretorio
            RAID_CONFIG['indiceParidade'] = quantDiscos - 1
            RAID_CONFIG['quantDiscosDados'] = quantDiscos - 1
            print("Configuração RAID carregada com sucesso.")
        else:
             RAID_CONFIG['quantDiscos'] = 0 # Invalida
             
    except ValueError:
        print("Entrada inválida. Tente novamente.")

def lerBloco(discoX, blocoDisco, config):
    caminho = os.path.join(config['diretorio'], f'disco{discoX}.bin')
    posFisica = blocoDisco * config['tamanhoBlocos']
    
    if not os.path.exists(caminho):
        # falha no disco
        print(f"AVISO: Disco{discoX}.bin não encontrado (falha). Retornando zeros.")
        return b'\x00' * config['tamanhoBlocos']

    with open(caminho, 'rb') as f: # Usa 'rb' para leitura simples
        f.seek(posFisica)
        return f.read(config['tamanhoBlocos'])
        
def escreverBloco(discoX, blocoDisco, dados, config):
    caminho = os.path.join(config['diretorio'], f'disco{discoX}.bin')
    posFisica = blocoDisco * config['tamanhoBlocos']
    
    if not os.path.exists(caminho):
        print(f"ERRO: Não é possível escrever no disco{discoX}.bin (falhou).")
        return

    # usando 'rb+' pois 'ab+' precisaria de seek e truncate
    # O modo 'rb+' garante a posição de escrita.
    with open(caminho, 'rb+') as f: 
        f.seek(posFisica)
        f.write(dados)

def escreveRAID():
    config = getConfig()
    if config['quantDiscos'] == 0:
        print("ERRO: RAID não inicializado ou carregado.")
        return
        
    print("\n--- 3. ESCREVER DADOS ---")
    
    # conversão string para bytes
    dados_a_gravar = input("Dados a gravar: ").encode('utf-8')
    # completa os dados com tamanho fixo de 100 bytes
    while len(dados_a_gravar) < 100:
        dados_a_gravar += b'0'
    # testando tamanho fixo
    #print(len(dados_a_gravar))
    try:
        posicaoInicioLogica = int(input(f"Posição de início (múltiplo de {config['tamanhoBlocos']}): "))
    except ValueError:
         print("Posição inválida.")
         return
    
    tamBloco = config['tamanhoBlocos']
    quantDados = config['quantDiscosDados']
    
    # escrita deve ser no início e ter tamanho do bloco
    if (posicaoInicioLogica % tamBloco != 0) or (len(dados_a_gravar) != tamBloco):
        print(f"ERRO: A escrita deve começar no início do bloco e ter {tamBloco} bytes.")
        return

    # posição de escrita (ex: Disco 1, Bloco 5)
    discoX, posFisica = posicaoLogica(
        posicaoInicioLogica, tamBloco, quantDados
    )
    blocoDisco = posFisica // tamBloco
    discoParidadeX = config['indiceParidade']
    
    print(f"Escrevendo no Disco D{discoX} no bloco {blocoDisco}...")
    
    # Obter o valor ANTIGO do bloco de DADOS
    caminhoDisco = os.path.join(config['diretorio'], f'disco{discoX}.bin')
    with open(caminhoDisco, 'rb') as arquivo:
        arquivo.seek(posFisica)
        blocoDadosAntigo = arquivo.read(tamBloco)
        
    # Obter o valor ANTIGO do bloco de PARIDADE correspondente
    blocoParidadeAntigo = lerBloco(discoParidadeX, blocoDisco, config)
    
    # paridade nova: Par_Nova = Par_Antiga XOR Disco_Antigo XOR Disco_Novo
    tempXor = calcularXorBytes([blocoParidadeAntigo, blocoDadosAntigo])
    blocoParidadeNovo = calcularXorBytes([tempXor, dados_a_gravar])

    # Escrever o NOVO bloco de DADOS
    escreverBloco(discoX, blocoDisco, dados_a_gravar, config)

    # Escrever o NOVO bloco de PARIDADE
    escreverBloco(discoParidadeX, blocoDisco, blocoParidadeNovo, config)
    
    print("Escrita e atualização da paridade concluídas.")

def leRAID():
    config = getConfig()
    if config['quantDiscos'] == 0:
        print("ERRO: RAID não inicializado ou carregado.")
        return
        
    print("\n--- 4. LER DADOS ---")  
    try:
        posicaoInicioLogica = int(input("Posição de início (em bytes): "))
        quantBytes = int(input("Quantidade de bytes a ler: "))
    except ValueError:
         print("Entrada inválida.")
         return
         
    tamBloco = config['tamanhoBlocos']
    quantDados = config['quantDiscosDados']
    bytesLidos = b''
    
    # Lógica de iteração de leitura bloco por bloco
    while len(bytesLidos) < quantBytes:
        
        posicaoAtualLogica = posicaoInicioLogica + len(bytesLidos)
        
        # Cálculo da posição física do *bloco inteiro* que contém a leitura
        discoDadosX, posFisicaB = posicaoLogica(
            posicaoAtualLogica, tamBloco, quantDados
        )
        blocoDisco = posFisicaB // tamBloco
        
        # Lógica de LEITURA COM RECUPERAÇÃO
        caminhoDisco = os.path.join(config['diretorio'], f'disco{discoDadosX}.bin')
        
        if os.path.exists(caminhoDisco):
            # Caso OK: Disco está OK, lê o bloco
            blocoDados = lerBloco(discoDadosX, blocoDisco, config)
        else:
            # Caso de FALHA: Reconstruir usando XOR dos outros
            print(f"RECUPERAÇÃO: Disco{discoDadosX}.bin falhou! Reconstruindo dados...")
            
            blocosXOR = []
            
            # Adicionar TODOS os blocos restantes (Dados e Paridade)
            for i in range(config['quantDiscos']):
                if i != discoDadosX:
                    blocosXOR.append(lerBloco(i, blocoDisco, config))
            
            # O XOR de todos os blocos restantes (incluindo P) resulta no bloco que faltava.
            blocoDados = calcularXorBytes(blocosXOR)
        
        # Ajusta o pedaço a ser lido do bloco (offset e tamanho)
        offsetInicial = posicaoAtualLogica % tamBloco
        bytesRestantesBloco = tamBloco - offsetInicial
        leituraBloco = min(quantBytes - len(bytesLidos), bytesRestantesBloco)
        
        bytesLidos += blocoDados[offsetInicial: offsetInicial + leituraBloco]

    try:
        dadosDecode = bytesLidos.decode('utf-8')
    except UnicodeDecodeError:
        dadosDecode = f"[Dados Binários: {bytesLidos}]"

    print(f"Resultado da Leitura ({len(bytesLidos)} bytes): {dadosDecode}")

def removeDiscoRAID():
    config = getConfig()
    if config['quantDiscos'] == 0:
        print("ERRO: RAID não inicializado ou carregado.")
        return
        
    print("\n--- 5. REMOVER DISCO ---")
    
    try:
        disco_a_remover = int(input(f"Índice do disco a remover (0 a {config['quantDiscos'] - 1}): "))
        if not (0 <= disco_a_remover < config['quantDiscos']):
             raise ValueError
    except ValueError:
         print("Índice inválido.")
         return
         
    caminhoArq = os.path.join(config['diretorio'], f'disco{disco_a_remover}.bin')
    
    if os.path.exists(caminhoArq):
        os.remove(caminhoArq)
        print(f"Disco {disco_a_remover} removido (arquivo apagado).")
    else:
        print("O disco já parecia estar removido.")

def constroiDiscoRAID():
    config = getConfig()
    if config['quantDiscos'] == 0:
        print("ERRO: RAID não inicializado ou carregado.")
        return
        
    print("\n--- 6. RECONSTRUIR DISCO ---")
    
    try:
        disco_a_construir = int(input(f"Índice do disco a reconstruir (0 a {config['quantDiscos'] - 1}): "))
        if not (0 <= disco_a_construir < config['quantDiscos']):
             raise ValueError
    except ValueError:
         print("Índice inválido.")
         return
         
    caminhoArq = os.path.join(config['diretorio'], f'disco{disco_a_construir}.bin')
    
    #verificando se o disco realmente precisa ser reconstruído
    if os.path.exists(caminhoArq):
         print(f"Disco{disco_a_construir}.bin já existe. Não é necessário reconstruir.")
         return
         
    print(f"Iniciando reconstrução do disco{disco_a_construir}.bin...")
    
    # Cria o novo arquivo vazio
    # Uso de 'wb' para criar e garantir o tamanho correto.
    #with open(caminhoArq, 'wb') as arquivo:
    #     pass
         
    tamanhoBloco = config['tamanhoBlocos']
    num_blocos_total = config['tamanhoDiscos'] // tamanhoBloco
    
    # Itera sobre todos os blocos
    for bloco_no_disco in range(num_blocos_total):
        
        blocos_para_xor = []
        
        # Lê o bloco correspondente de TODOS os outros discos (Dados + Paridade)
        for i in range(config['quantDiscos']):
            if i != disco_a_construir:
                blocos_para_xor.append(lerBloco(i, bloco_no_disco, config))
                
        # O XOR de todos os blocos restantes gera o bloco perdido
        bloco_reconstruido = calcularXorBytes(blocos_para_xor)
        
        # Escreve o bloco reconstruído no novo disco
        escreverBloco(disco_a_construir, bloco_no_disco, bloco_reconstruido, config)
        
    print(f"Reconstrução do disco{disco_a_construir}.bin concluída com sucesso!")

'''def inicializaRAID():
    quantDiscos = int(input('Quantidade de discos: '))
    tamanhoDiscos = int(input('Tamanho de cada disco (em bytes): '))
    tamanhoBlocos = int(input('Tamanho de blocos dos discos (em bytes): '))
    pasta = input('Nome da pasta dos arquivos: ')

    diretorio = os.makedirs(pasta, exist_ok=True)

    for disco in range(quantDiscos - 1): # -1 pois haverá outra linha apenas para a criaçao do disco de paridade
        open(f'{diretorio}\\disco{disco}.bin', '+ab')


def obtemRAID()
    
def escreveRAID()
    
def leRAID()
    
def removeDiscoRAID()
    
def constroiDiscoRAID()'''
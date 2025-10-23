import hashlib; from time import time

def findNonce(dataToHash: bytes, bitsZero: int):
    inicio = time()
    nonce = 0
    while True:
        bytesInput = nonce.to_bytes(4, 'big') + dataToHash

        target = 1 << (256 - bitsZero)
        hashDigest = hashlib.sha256(bytesInput).digest()
        intHash = int.from_bytes(hashDigest, 'big')

        if intHash < target:
            tempoDec = time() - inicio

        nonce += 1
        return nonce, tempoDec   

def findNonceHex(dataToHash: bytes, bitsZero: int):
    inicio = time()
    nonce = 0
    while True:
        bytesInput = nonce.to_bytes(4, 'big') + dataToHash

        hashDigest = hashlib.sha256(bytesInput).hexdigest()
        if hashDigest.startswith('0' * ((bitsZero // 4) + (bitsZero % 4))):
            tempoDec = time() - inicio 
            return nonce, tempoDec
             
        nonce += 1           

#strBinTestes = 'É possivel calcular essa?'.encode()
lstEntrada = [['Esse é facil', 8], ['Esse é facil', 10], ['Esse é facil', 15],
              ['Texto maior muda o tempo?', 8], ['Texto maior muda o tempo?', 10], ['Texto maior muda o tempo?', 15],
              ['É possível calcular esse?', 18], ['É possível calcular esse?', 19], ['É possível calcular esse?', 20]]
#intDificuldade = 18
nonce = 0

#while True:
for texto in lstEntrada:
    nonceEncontrado, tempoDecorrido = findNonce(texto[0].encode(), texto[1])
    nonce2, tempo2 = findNonceHex(texto[0].encode(), texto[1])

    print(f'NONCE: {nonceEncontrado} TEMPO: {tempoDecorrido:.4f} s')
    print(f'NONCE: {nonce2} TEMPO: {tempo2:.4f} s')
    
# COMPARAR FUNCOES COM DIGEST E HEXDIGEST

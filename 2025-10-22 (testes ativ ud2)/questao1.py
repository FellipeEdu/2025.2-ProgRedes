import hashlib; from time import time

def findNonce(dataToHash: bytes, bitsZero: int):
    while True:
        bytesInput = nonce.to_bytes(4, 'big') + dataToHash

        target = 1 << (256 - bitsZero)
        hashDigest = hashlib.sha256(bytesInput).digest()
        intHash = int.from_bytes(hashDigest, 'big')

        if intHash < target:
            tempoDec = time() - inicio
            #print(f'HASH: {hashDigest}')
            #print(f'NONCE: {nonce} TEMPO: {tempoDec:.4f} s')
            return nonce, tempoDec   
        nonce += 1

#strBinTestes = 'É possivel calcular essa?'.encode()
lstEntrada = [['Esse é facil', 8], ['Esse é facil', 10], ['Esse é facil', 15],
              ['Texto maior muda o tempo?', 8], ['Texto maior muda o tempo?', 10], ['Texto maior muda o tempo?', 15],
              ['É possível calcular esse?', 18], ['É possível calcular esse?', 19], ['É possível calcular esse?', 20]]
#intDificuldade = 18
nonce = 0
inicio = time()

#while True:
for texto in lstEntrada:
    nonceEncontrado, tempoDecorrido = findNonce(texto[0], texto[1])
    print(f'NONCE: {nonceEncontrado} TEMPO: {tempoDecorrido:.4f} s')

# tempoDecorrido = time() - inicio

#print(f'NONCE: {nonce} TEMPO: {tempoDecorrido:.4f} s')

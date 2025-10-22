import hashlib; from time import time

strBinTestes = 'É possivel calcular essa?'.encode()
intDificuldade = 18
nonce = 0
inicio = time()

while True:
    bytesInput = nonce.to_bytes(4, 'big') + strBinTestes

    #hashResultado = hashlib.sha256(bytesInput).hexdigest()
    #if hashResultado.startswith('0' * ((intDificuldade // 4) + (intDificuldade % 4))): break

    hashResultado = hashlib.sha256(bytesInput).digest()
        
    nonce += 1
        
tempoDecorrido = time() - inicio

print(f'HASH: {hashResultado} NONCE: {nonce} TEMPO: {tempoDecorrido:.4f} s')

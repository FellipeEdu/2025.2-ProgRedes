strIP = '192.168.1.10'

# --------------------------------------------------
# Gerando uma lista com 4 posições
# Cada posição é o inteiro correspondente a cada octeto do IP

lstIP = [int(x) for x in strIP.split(".")]
print(lstIP)

# Será impresso -> [192, 168, 1, 10]

# --------------------------------------------------
# Convertendo a lista em bytes, onde cada posição da 
# lista vira um byte
binIP = bytes(lstIP)

print(binIP)
# Será impresso -> b'\xc0\xa8\x01\n'

# converter pra inteiro
intIP = int.from_bytes
'''
   Exemplo 01 - Convertendo um endereço IP em inteiro de 32 bits
'''
strIP = '192.168.1.10'
print(f'O Endereço IPv4 é.....................: {strIP}\n')

lstIP = [int(x) for x in strIP.split(".")]

print(f'Lista de inteiros (octetos)...........: {lstIP}\n')

bytesIP = bytes(lstIP)

print(f'Endereço IPv4 como bytes..............: {bytesIP}\n')

intIP = int.from_bytes(bytes(lstIP), byteorder='big')

print(f'Endereço IPv4 como inteiro ...........: {intIP}\n')

print(f'O Endereço IPv4 em binário é (32 bits): {intIP:032b}\n')  

#

'''strIP = '255.255.255.0'

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
intIP = int.from_bytes(bytes(lstIP), byteorder="big")

print(f'int IP...: {intIP}')'''
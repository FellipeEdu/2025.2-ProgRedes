'''intCIDR = 24

intMascara = 0xFFFFFFFF >> (32 - intCIDR)

intMascara = intMascara << (32 - intCIDR)'''

# Será impresso -> 4294967040 (4.294.967.040)

strIP   = '192.168.1.10'
intCIDR = 24

intIP      = int.from_bytes(bytes([int(x) for x in strIP.split('.')]) ,'big')

intMascara = 0xFFFFFFFF >> (32 - intCIDR) << (32 - intCIDR)
print(intMascara)
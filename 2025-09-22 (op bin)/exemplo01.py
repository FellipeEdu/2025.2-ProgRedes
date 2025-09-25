import sys

try:
    intValor = int(input('Digite um numero inteiro: '))
except ValueError:
    sys.exit('Valor inválido')
except KeyboardInterrupt:
    sys.exit('\nPrograma interrompido pelo usuário.')
except Exception as erro:
    sys.exit(f'Erro: {erro}.')
else:
    '''print(f'{intValor} em Binário...: {bin(intValor):08b}')

    print(f'{intValor} em Hexadecimal...: {hex(intValor)}')

    print(f'{intValor} em Octal...: {oct(intValor)}')'''

    if intValor < 0:
        sys.exit('Por favor, insira um numero inteiro não negativo.')
    
    intQuantBits = intValor.bit_length()

    # converter pra bin e remover '0b'
    binValor = bin(intValor)[2:]

    if len(binValor) % 8 != 0:
        # quantos zeros sao necessarios pra completar o byte
        intZeros = 8 - len(binValor) % 8

    # add os zeros a esquerda
    binValorFinal = ('0' * intZeros) + binValor

    print(f'\n{intValor} em Binário...: 0b{binValorFinal}')
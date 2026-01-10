import socket, os
from constantes import HOST_IP_SERVER, DIR_IMG_CLIENT
from funcoes import dir_Existe, solicitar_Arq

os.system('cls') if os.name == 'nt' else os.system('clear')

print('\n' + '-' * 100)
print('CLIENTE TCP - Enviando pedidos de arquivo...')
print('Digite SAIR para encerrar o cliente.\n')
print(f'IP/Porta do Cliente: {("", "auto")}')
print('-' * 100 + '\n')

'''server_host = input('IP do servidor (ex: 127.0.0.1): ').strip()
if not server_host:
    server_host = '127.0.0.1'''
dir_Existe(DIR_IMG_CLIENT)

while True:
   print(f"{'=' * 10} Menu {'=' * 10}")
   print("1. Solicitar Arquivo")
   print("2. tbd")
   print("3. tbd")
        
   escolha = input("Escolha uma opção: ")
   
   # Solicitar arquivo
   if escolha == '1': 
      nome = input('\nDigite o arquivo para receber: ').strip()
      if not nome:
         continue
      solicitar_Arq(nome)
   # Sair
   elif escolha.lower() == 'sair':
      break

   print(f'\n{'*' * 30}')

   '''elif escolha == '2':
      funcoes.obtemRAID()
   elif escolha == '3':
      funcoes.escreveRAID()'''

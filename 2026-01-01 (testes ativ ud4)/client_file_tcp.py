import socket, os
from constantes import DIR_IMG_CLIENT
from funcoes import dir_Existe, solicitar_Arq, listar_Arquivos

os.system('cls') if os.name == 'nt' else os.system('clear')

print(f"{'-' * 100}\n")
print('CLIENTE TCP - Enviando pedidos de arquivo...')
print('Digite SAIR para encerrar o cliente.\n')
print(f'IP/Porta do Cliente: {("", "auto")}')
print(f"{'-' * 100}\n")

'''server_host = input('IP do servidor (ex: 127.0.0.1): ').strip()
if not server_host:
    server_host = '127.0.0.1'''
dir_Existe(DIR_IMG_CLIENT)

while True:
   print(f"{'=' * 10} Menu {'=' * 10}")
   print("1. Solicitar Arquivo")
   print("2. Listar Arquivos")
   print("3. tbd")
        
   escolha = input("Escolha uma opção: ")
   
   # Solicitar arquivo
   if escolha == '1': 
      nome = input('\nDigite o arquivo para receber: ').strip()
      if not nome:
         continue
      solicitar_Arq(nome)
   # Listar arquivos
   elif escolha == '2':
      lista = listar_Arquivos()
      if lista is None:
         print('Não foi possível obter a listagem do servidor.')
      elif not lista:
         print('Nenhum arquivo disponível no servidor.')
      else:
         print('\nArquivos disponíveis:')

         for num, item in enumerate(lista, start=1):
               nome = item.get('nome')
               tamanho = item.get('tamanho',)
               print(f'{num:2d}. {nome} ({tamanho} bytes)')
   # Upload de arquivos
   # elif  escolha == '3':

   # Sair
   elif escolha.lower() == 'sair':
      break
   else:
      print("Opção inválida")

   print(f"\n{'*' * 30}")

   '''
   elif escolha == '3':
      funcoes.escreveRAID()'''

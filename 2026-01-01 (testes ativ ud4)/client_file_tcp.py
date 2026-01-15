import socket, os
from constantes import DIR_IMG_CLIENT
from funcoes import dir_Existe, solicitar_Arq, listar_Arquivos, upload_Arquivo, solicitar_Parcial

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
   print("1. Download de Arquivo")
   print("2. Listar Arquivos")
   print("3. Fazer Upload de Arquivo")
   print("4. Download Parcial de Arquivo")
   #print("4. Download Parcial de Arquivo")
        
   escolha = input("Escolha uma opção: ")
   
   # Solicitar arquivo
   if escolha == '1': 
      nome = input('Nome do arquivo a receber: ').strip()
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
   elif escolha == '3':
      nome_Atual_Arq = input("Nome do arquivo que deseja enviar: ").strip()
      nome_Novo_Arq = input("Nome do arquivo no servidor (deixar em branco para mesmo nome): ").strip()

      if not nome_Atual_Arq:
         print('Nome inválido. Tente novamente.')
         continue

      if nome_Novo_Arq:
         upload_Arquivo(nome_Atual_Arq, nome_Dest=nome_Novo_Arq)
      else:
         upload_Arquivo(nome_Atual_Arq)
   # Download Parcial
   elif escolha == '4':
      nome_parcial = input('\nNome do arquivo: ').strip()
      if not nome_parcial:
         continue
      pos_text = input('Posição inicial em bytes (deixar em branco = tamanho atual do arquivo): ').strip()
      if pos_text == '':
         posicao = None
      else:
         try:
             posicao = int(pos_text)
             if posicao < 0:
                 print('Posição deve ser >= 0.\n')
                 continue
         except ValueError:
             print('Posição inválida. Informe um número inteiro.\n')
             continue

      success = solicitar_Parcial(nome_parcial, posicao_Inicial=posicao)
      if not success:
         print('Falha no download parcial.\n')
   # n sei
   # elif escolha == '5':
   # Sair
   elif escolha.lower() == 'sair':
      break
   else:
      print("Opção inválida")

   print(f"\n{'*' * 30}")

   '''
   elif escolha == '3':
      funcoes.escreveRAID()'''

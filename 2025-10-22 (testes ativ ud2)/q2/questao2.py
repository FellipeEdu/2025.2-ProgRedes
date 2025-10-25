import funcoes

while True:
        print(f"\n{'=' * 10} Menu RAID Simulator {'=' * 10}")
        print("1. inicializaRAID (Cria e Zera Discos)")
        print("2. obtemRAID (Carrega Config. Existente)")
        print("3. escreveRAID (Gravar Dados)")
        print("4. leRAID (Ler Dados)")
        print("5. removeDiscoRAID (Simular Falha)")
        print("6. constroiDiscoRAID (Reconstruir Disco)")
        print("0. Sair")
        
        escolha = input("Escolha uma opção: ")
        
        if escolha == '1':
            funcoes.inicializaRAID()
        elif escolha == '2':
            funcoes.obtemRAID()
        elif escolha == '3':
            funcoes.escreveRAID()
        elif escolha == '4':
            funcoes.leRAID()
        elif escolha == '5':
            funcoes.removeDiscoRAID()
        elif escolha == '6':
            funcoes.constroiDiscoRAID()
        elif escolha == '0':
            print('Encerrando o simulador.')
            break
        else:
            print('Opção inválida.')
import os
import socket
import json
import hashlib
from constantes import *

# --- utilitários ---
def dir_Existe(caminho):
    if not os.path.exists(caminho):
        os.makedirs(caminho, exist_ok=True)

def safe_join(base, *caminhos):
    """Evita path traversal: ensures returned path is inside base."""
    arq_Teste = os.path.abspath(os.path.join(base, *caminhos))
    base_abs = os.path.abspath(base)
    if not (arq_Teste == base_abs or arq_Teste.startswith(base_abs + os.sep)):
        raise ValueError("Escape da pasta não permitido")
    return arq_Teste

def send_Tudo(socket, dados):
    """Envia todos os bytes de data por meio do socket em um loop. Usa sock.send até que todo o conteúdo seja enviado."""
    total_Enviado = 0
    while total_Enviado < len(dados):
        enviado = socket.send(dados[total_Enviado:])
        if enviado == 0:
            raise RuntimeError("Conexão de socket quebrada durante send.")
        total_Enviado += enviado

def recv_Tudo(socket, n_Bytes):
    """lê exatamente n bytes do socket. Faz recv repetidas vezes até completar n bytes; se o socket fechar antes retorna None."""
    dados = b''
    while len(dados) < n_Bytes:
        bloco = socket.recv(n_Bytes - len(dados))
        if not bloco:
            return None
        dados += bloco
    return dados

def int_Bytes_BE(int_Valor):    return int(int_Valor).to_bytes(4, byteorder='big', signed=False)

def bytes_Int_BE(bytes_Valor):  return int.from_bytes(bytes_Valor, byteorder='big', signed=False)

def prefixo_MD5(caminho_Arq, length):
    """
    Retorna o digest MD5 (16 bytes) dos primeiros `length` bytes do arquivo.
    Se length == 0 retorna o MD5 do prefixo vazio (sem ler o arquivo).
    """
    if length == 0:
        return hashlib.md5(b'').digest()
    md5 = hashlib.md5()
    lido = 0
    with open(caminho_Arq, 'rb') as arquivo:
        while lido < length:
            para_Ler = min(BUFFER_SIZE, length - lido)
            bloco = arquivo.read(para_Ler)
            if not bloco:
                break
            md5.update(bloco)
            lido += len(bloco)
    return md5.digest()

# --- funções do servidor (usam EOF como delimitador de fim de arquivo) ---
def stream_Arquivo(socket, caminho_Arq):
    """Envia o conteúdo do arquivo em blocos usando send_all."""
    with open(caminho_Arq, 'rb') as arquivo:
        while True:
            bloco = arquivo.read(BUFFER_SIZE)
            if not bloco: break
            send_Tudo(socket, bloco)

def unica_Conexao(conexao, cliente):
    """
    Lê uma requisição do cliente e responde com:
      - 1 byte status + 4 bytes tamanho + blocos de dados (payload)
    Suporta as operações:
      - OP_DOWNLOAD (10): cliente envia 1 byte op + 4 bytes len(nome) + nome
          -> servidor responde com status + 4 bytes tamanho + arquivo
      - OP_LIST (20): cliente envia 1 byte op
          -> servidor responde com status + 4 bytes tamanho + payload JSON
      - OP_UPLOAD (30): cliente envia 1 byte op + 4 bytes len(nome) + nome
          -> servidor responde com 1 byte (accept: 1 / refuse: 0)
          se aceito cliente envia 4 bytes tamanho + dados do arquivo
          -> servidor responde com 1 byte final (success:1 / error:0)
    Observação: usa helpers no escopo: recv_Tudo, send_Tudo, bytes_Int_BE, int_Bytes_BE, safe_join, stream_Arquivo,
    DIR_IMG_SERVER, CODE_PAGE, STATUS_OK, STATUS_ERRO, STATUS_NOT_FOUND, OP_DOWNLOAD, OP_LIST, OP_UPLOAD
    """
    try:
        print(f'Conexão de {cliente}')

        # lê 1 byte inicial (pode ser OP_LIST ou o primeiro byte do tamanho do nome)
        primeiro_byte = recv_Tudo(conexao, 1)
        if not primeiro_byte:
            print('ERRO: Pedido mal formado (sem dados iniciais).\n')
            return
        
        print(f"OP_CODE: {bytes_Int_BE(primeiro_byte)}")
        # 10
        if primeiro_byte[0] == OP_DOWNLOAD:
            # --- operação GET (recebeu o primeiro byte do tamanho do nome) ---
            # precisamos ler os 3 bytes restantes para completar os 4 bytes do tamanho
            bytes_Tam = recv_Tudo(conexao, 4)
            if bytes_Tam is None:
                print('ERRO: Pedido mal formado (tamanho incompleto).\n')
                return
            tam_Nome = bytes_Int_BE(bytes_Tam)
            '''#debug
            print(bytes_Tam)
            print(bytes_Int_BE(bytes_Tam))'''
            
            '''#debug
            print(bytes_Nome)
            print(bytes_Int_BE(bytes_Nome))'''
            bytes_Nome = recv_Tudo(conexao, tam_Nome)
            if bytes_Nome is None:
                print('ERRO: Pedido mal formado (nome incompleto).\n')
                return
            nome_Arq = bytes_Nome.decode(CODE_PAGE)
            print(f'Requisição de arquivo: {nome_Arq}')

            try:
                caminho = safe_join(DIR_IMG_SERVER, nome_Arq)
            except ValueError:
                msg_Erro = 'ERRO: Caminho inválido'
                dados_Enviados = msg_Erro.encode(CODE_PAGE)
                send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                return

            if not os.path.isfile(caminho):
                msg_Erro = 'ERRO: Arquivo não encontrado'
                dados_Enviados = msg_Erro.encode(CODE_PAGE)
                send_Tudo(conexao, bytes([STATUS_NOT_FOUND]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                return

            tam_Arquivo = os.path.getsize(caminho)
            # envia header com status OK e tamanho do arquivo, depois o arquivo em si
            send_Tudo(conexao, bytes([STATUS_OK]) + int_Bytes_BE(tam_Arquivo))
            stream_Arquivo(conexao, caminho)
            print(f'Envio concluído: {nome_Arq}\n')
        # 20
        elif primeiro_byte[0] == OP_LIST:
            # --- operação LIST ---
            print("Requisição de Lista de Arquivos.")

            try:
                entradas = []
                for nome in os.listdir(DIR_IMG_SERVER):
                    caminho = os.path.join(DIR_IMG_SERVER, nome)
                    if os.path.isfile(caminho):
                        tamanho = os.path.getsize(caminho)
                        entradas.append({'nome': nome, 'tamanho': str(tamanho)})
                texto_Dados = json.dumps(entradas)
                dados_Enviados = texto_Dados.encode(CODE_PAGE)
                send_Tudo(conexao, bytes([STATUS_OK]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)

                print("Envio concluído.\n")
                return
            except Exception as erro:
                try:
                    msg_Erro = f'ERRO: {erro}'.encode(CODE_PAGE)
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(msg_Erro)) + msg_Erro)
                except Exception:
                    pass
                return
        # 30    
        elif primeiro_byte[0] == OP_UPLOAD:
             # recebe 4 bytes com o tamanho do nome do arquivo
            bytes_Tam = recv_Tudo(conexao, 4)
            if bytes_Tam is None:
                print('ERRO: Pedido de upload mal formado (tamanho ausente).')
                return
            tam_Nome = bytes_Int_BE(bytes_Tam)

            # validação básica
            if tam_Nome <= 0 or tam_Nome > 10000:
                print(f'ERRO: tam_Nome inválido ({tam_Nome}).')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return

            bytes_Nome = recv_Tudo(conexao, tam_Nome)
            if bytes_Nome is None:
                print('ERRO: Pedido de upload mal formado (nome incompleto).')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return

            # decodifica e sanitiza nome (remove espaços em volta)
            nome_Arq = bytes_Nome.decode(CODE_PAGE).strip()
            print(f'Requisição de upload: {nome_Arq!r}')

            # nome não pode ser vazio
            if not nome_Arq:
                print('ERRO: nome de arquivo vazio no pedido de upload.')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return

            # tenta construir caminho seguro dentro da pasta do servidor
            try:
                caminho_dest = safe_join(DIR_IMG_SERVER, nome_Arq)
            except ValueError:
                print('ERRO: Upload recusado - caminho inválido/fora da pasta do usuário.')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))  # recusa
                except:
                    pass
                return

            # responde ACEITO (1)
            try:
                send_Tudo(conexao, bytes([STATUS_OK]))
            except Exception as erro:
                print(f'ERRO ao enviar aceitação para upload: {erro}')
                return

            # agora espera 4 bytes com o tamanho do arquivo
            bytes_Tam = recv_Tudo(conexao, 4)
            if bytes_Tam is None:
                print('ERRO: Upload mal formado (tamanho do arquivo ausente).')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return
            tam_Arquivo = bytes_Int_BE(bytes_Tam)

            # validação do tamanho (evita alocar/esperar descrepâncias absurdas)
            tam_Max = 200 * 1024 * 1024  # 200 MB por segurança; ajuste se necessário
            if tam_Arquivo < 0 or tam_Arquivo > tam_Max:
                print(f'ERRO: tam_Arquivo inválido/maior que limite ({tam_Arquivo}).')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return

            # grava o arquivo recebendo exatamente tam_Arquivo bytes
            try:
                # garante diretório existente
                dir_Existe(os.path.dirname(caminho_dest) or DIR_IMG_SERVER)
                with open(caminho_dest, 'wb') as arquivo:
                    indice = tam_Arquivo
                    while indice > 0:
                        para_Ler = min(BUFFER_SIZE, indice)
                        bloco = recv_Tudo(conexao, para_Ler)
                        if bloco is None:
                            # conexão fechou no meio do upload
                            print('ERRO: conexão encerrada durante upload.')
                            try:
                                arquivo.close()
                            except:
                                pass
                            try:
                                os.remove(caminho_dest)
                            except:
                                pass
                            try:
                                send_Tudo(conexao, bytes([STATUS_ERRO]))
                            except:
                                pass
                            return
                        arquivo.write(bloco)
                        indice -= len(bloco)
                # upload concluído com sucesso
                print(f'Upload concluído: {nome_Arq} ({tam_Arquivo} bytes)\n')
                try:
                    send_Tudo(conexao, bytes([STATUS_OK]))
                except:
                    pass
                return
            except PermissionError as perm_err:
                print(f'ERRO durante recebimento do upload: Permissão negada ao gravar "{caminho_dest}": {perm_err}')
                try:
                    # tenta remover arquivo parcial se existir
                    if os.path.exists(caminho_dest) and not os.path.isdir(caminho_dest):
                        os.remove(caminho_dest)
                except:
                    pass
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return
            except Exception as erro:
                print(f'ERRO durante recebimento do upload: {erro}')
                # tentativa de remover arquivo parcial
                try:
                    if os.path.exists(caminho_dest) and not os.path.isdir(caminho_dest): os.remove(caminho_dest)
                except:
                    pass
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]))
                except:
                    pass
                return
        # 40
        elif primeiro_byte[0] == OP_RESUME:
             # recebe 4 bytes com o tamanho do nome do arquivo
            bytes_Tam = recv_Tudo(conexao, 4)
            if bytes_Tam is None:
                print('ERRO: Pedido parcial mal formado (tamanho ausente).\n')
                return
            tam_Nome = bytes_Int_BE(bytes_Tam)

            if tam_Nome <= 0 or tam_Nome > 10000:
                print(f'ERRO: tam_Nome inválido ({tam_Nome}).\n')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(0))
                except:
                    pass
                return

            bytes_Nome = recv_Tudo(conexao, tam_Nome)
            if bytes_Nome is None:
                print('ERRO: Pedido parcial mal formado (nome incompleto).\n')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(0))
                except:
                    pass
                return

            nome_Arq = bytes_Nome.decode(CODE_PAGE).strip()
            print(f'Requisição parcial: {nome_Arq}\n')

            # lê 4 bytes com a posição inicial (uint32 BE)
            bytes_Posicao = recv_Tudo(conexao, 4)
            if bytes_Posicao is None:
                print('ERRO: Pedido parcial mal formado (posição ausente).\n')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(0))
                except:
                    pass
                return
            pos_Inicial = bytes_Int_BE(bytes_Posicao)

            # lê 16 bytes com o MD5 (digest raw)
            md5_Recebido = recv_Tudo(conexao, 16)
            if md5_Recebido is None:
                print('ERRO: Pedido parcial mal formado (MD5 ausente).\n')
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(0))
                except:
                    pass
                return

            # valida caminho seguro
            try:
                caminho = safe_join(DIR_IMG_SERVER, nome_Arq)
            except ValueError:
                msg = 'ERRO: Caminho inválido'
                dados_Enviados = msg.encode(CODE_PAGE)
                try:
                    send_Tudo(conexao, bytes([STATUS_NOT_FOUND]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                except:
                    pass
                return

            if not os.path.isfile(caminho):
                msg = 'ERRO: Arquivo não encontrado'
                dados_Enviados = msg.encode(CODE_PAGE)
                try:
                    send_Tudo(conexao, bytes([STATUS_NOT_FOUND]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                except:
                    pass
                return

            tam_Arquivo = os.path.getsize(caminho)

            # valida posição
            if pos_Inicial > tam_Arquivo:
                msg = 'ERRO: Posição inicial maior que tamanho do arquivo\n'
                dados_Enviados = msg.encode(CODE_PAGE)
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                except:
                    pass
                return

            ''# calcula MD5 do prefixo no servidor e compara (otimizado para pos_inicial == 0)
            try:
                server_MD5 = prefixo_MD5(caminho, pos_Inicial)
            except Exception as erro:
                msg = f'ERRO: falha ao calcular MD5: {erro}'
                dados_Enviados = msg.encode(CODE_PAGE)
                try:
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                except:
                    pass
                return''

            if server_MD5 != md5_Recebido:
                msg = 'ERRO: MD5 inválido (parte local difere do servidor)'
                dados_Enviados = msg.encode(CODE_PAGE)
                try:
                    send_Tudo(conexao, bytes([STATUS_HASH_INVALIDO]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
                except:
                    pass
                return

            # MD5 ok -> envia status OK + 4 bytes com o tamanho restante, depois os dados a partir da posição
            restante = tam_Arquivo - pos_Inicial
            try:
                send_Tudo(conexao, bytes([STATUS_OK]) + int_Bytes_BE(restante))
                with open(caminho, 'rb') as arquivo:           
                    arquivo.seek(pos_Inicial)
                    indice = restante
                    while indice > 0:
                        bloco = arquivo.read(min(BUFFER_SIZE, indice))
                        if not bloco:
                            break
                        send_Tudo(conexao, bloco)
                        indice -= len(bloco)

                print(f'Parcial enviado: {nome_Arq} (a partir de {pos_Inicial}) ; {restante} bytes\n')

            except Exception as erro:
                print(f'ERRO durante envio parcial: {erro}\n')
                try:
                    msg = f'ERRO: {erro}'.encode(CODE_PAGE)
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(msg)) + msg)
                except:
                    pass
            return

    except Exception as erro:
        try:
            msg_Erro = f'ERRO: {erro}'.encode(CODE_PAGE)
            send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(msg_Erro)) + msg_Erro)
        except Exception:
            pass
    finally:
        try:
            conexao.close()
        except:
            pass

# --- funções do cliente: agora com server_host como parâmetro explícito ---
# 10
def solicitar_Arq(nome):
    """
    Conecta ao servidor indicado por server_host e solicita o arquivo.

    Conecta a server_host e solicita filename.
    Envia: 4 bytes len(nome) + nome
    Recebe: 1 byte status + 4 bytes tamanho + payload
    """
    #if pasta_Dest is None: pasta_Dest = DIR_IMG_CLIENT
    dir_Existe(DIR_IMG_CLIENT)
    caminho_Dest = os.path.join(DIR_IMG_CLIENT, nome)

    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((HOST_IP_SERVER, HOST_PORT))

        # envia nome com 4 bytes de comprimento
        bytes_Nome = nome.encode(CODE_PAGE)
        send_Tudo(tcp_Socket, bytes([OP_DOWNLOAD]) + int_Bytes_BE(len(bytes_Nome)) + bytes_Nome)

        # lê 1 byte de status
        bytes_Status = recv_Tudo(tcp_Socket, 1)
        if not bytes_Status:
            print('Sem resposta do servidor.')
            return False
        status = bytes_Status[0]

        # lê 4 bytes tamanho
        bytes_Tam = recv_Tudo(tcp_Socket, 4)
        if bytes_Tam is None:
            print('Resposta mal formada do servidor.')
            return False
        tam_Dados = bytes_Int_BE(bytes_Tam)

        # lê payload exatamente payload_size bytes (pode ser grande; lê em loop)
        restante = tam_Dados
        dir_Existe(DIR_IMG_CLIENT)
        if status == STATUS_OK:
            with open(caminho_Dest, 'wb') as arquivo:
                while restante > 0:
                    para_Ler = min(BUFFER_SIZE, restante)
                    bloco = recv_Tudo(tcp_Socket, para_Ler)
                    if bloco is None:
                        print('Conexão encerrada inesperadamente.')
                        return False
                    arquivo.write(bloco)
                    restante -= len(bloco)
            print(f'Arquivo recebido: {caminho_Dest}')
            return True
        else:
            # payload é mensagem de erro/descrição — lê tudo (pode ser 0)
            msg = b''
            if tam_Dados > 0:
                msg = recv_Tudo(tcp_Socket, tam_Dados) or b''
            try:
                print(msg.decode(CODE_PAGE, errors='ignore'))
            except:
                print('\nErro do servidor (mensagem binária).')
            return False

    except socket.timeout:
        print('\nTimeout: sem resposta do servidor.')
        return False
    except FileNotFoundError:
        print('\nErro ao criar arquivo local.')
        return False
    except socket.error as erro_Socket:
        print(f'\nErro de socket: {erro_Socket}')
        return False
    except Exception as erro:
        print(f'\nErro genérico: {erro}')
        return False
    finally:
        if tcp_Socket:
            try:
                tcp_Socket.close()
            except:
                pass
# 20
def listar_Arquivos():
    """
    Solicita a listagem de arquivos ao servidor.

    Protocolo (cliente -> servidor):
      - 1 byte: operação (valor 20 para LIST)

    Resposta (servidor -> cliente):
      - 1 byte: status (constantes.STATUS_OK == sucesso)
      - 4 bytes: payload size (uint32 big-endian)
      - payload: JSON com a listagem: [ {'nome': 'arquivo1.txt', 'tamanho': '12345'}, ... ]

    Retorna:
      - lista Python (decodificada do JSON) em caso de STATUS_OK
      - None em caso de erro (imprime mensagem)
    """
    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((HOST_IP_SERVER, HOST_PORT))

        # obtém o código da operação (usa constante se existir, senão 20)
        #OP_LIST = getattr(constantes, 'OP_LIST', 20)
        send_Tudo(tcp_Socket, bytes([OP_LIST]))

        # lê 1 byte de status
        bytes_Status = recv_Tudo(tcp_Socket, 1)
        if not bytes_Status:
            print('\nSem resposta do servidor.')
            return None
        status = bytes_Status[0]

        # lê 4 bytes com o tamanho do payload
        bytes_Tam = recv_Tudo(tcp_Socket, 4)
        if bytes_Tam is None:
            print('\nResposta malformada do servidor (tamanho ausente).')
            return None
        tam_Dados = bytes_Int_BE(bytes_Tam)

        # lê o payload completo (pode ser 0)
        dados_Enviados = b''
        if tam_Dados > 0:
            dados_Enviados = recv_Tudo(tcp_Socket, tam_Dados)
            if dados_Enviados is None:
                print('\nConexão encerrada inesperadamente durante o recebimento dos dados.')
                return None

        if status == STATUS_OK:
            # payload esperado em JSON -> decodifica e retorna lista
            try:
                texto = dados_Enviados.decode(CODE_PAGE)
                dados = json.loads(texto)
                #print(dados)
                return dados
            except Exception as erro:
                print(f'\nErro ao decodificar JSON da listagem: {erro}')
                return None
        else:
            # payload é mensagem de erro textual
            try:
                msg = dados_Enviados.decode(CODE_PAGE, errors='ignore')
                print(f'\nServidor retornou erro na listagem: {msg}')
            except Exception:
                print('\nServidor retornou erro na listagem (mensagem binária).')
            return None

    except socket.timeout:
        print('\nTimeout: sem resposta do servidor.')
        return None
    except socket.error as erro_Socket:
        print(f'\nErro de socket: {erro_Socket}')
        return None
    except Exception as erro:
        print(f'\nErro genérico: {erro}')
        return None
    finally:
        if tcp_Socket:
            try:
                tcp_Socket.close()
            except:
                pass
# 30
def upload_Arquivo(nome_Arquivo, nome_Dest=None):
    """
    Envia um arquivo que está na pasta client_files para o servidor via OP_UPLOAD.

    Parâmetros:
      - nome_arquivo: nome do arquivo existente em DIR_IMG_CLIENT (ex: 'foto.jpg')
      - server_Host: IP/host do servidor (opcional, default HOST_IP_SERVER)
      - nome_dest: nome que será usado no servidor (opcional; se None ou '' usa nome_arquivo)

    Retorna True em sucesso, False em erro.
    """
    # evita path traversal no lado cliente: usa sempre basename
    nome_local_seguro = os.path.basename(nome_Arquivo)
    caminho_local = os.path.join(DIR_IMG_CLIENT, nome_local_seguro)

    if not os.path.isfile(caminho_local):
        print('\nErro: arquivo local não encontrado em DIR_IMG_CLIENT.')
        return False

    # se nome_dest for None ou string vazia, usa o próprio nome_local_seguro
    if not nome_Dest:
        nome_Dest = nome_local_seguro

    try:
        bytes_Nome = nome_Dest.encode(CODE_PAGE)
    except Exception as erro:
        print(f'\nErro ao codificar nome do arquivo: {erro}')
        return False

    tam_Arquivo = os.path.getsize(caminho_local)

    # mesma validação do servidor (ajuste se necessário)
    tam_Max = 200 * 1024 * 1024  # 200 MB
    if tam_Arquivo < 0 or tam_Arquivo > tam_Max:
        print(f'\nErro: arquivo muito grande ({tam_Arquivo} bytes). Limite: {tam_Max} bytes.')
        return False

    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((HOST_IP_SERVER, HOST_PORT))

        # envia: opcode + 4 bytes len(nome) + nome
        header = bytes([OP_UPLOAD]) + int_Bytes_BE(len(bytes_Nome)) + bytes_Nome
        send_Tudo(tcp_Socket, header)

        # aguarda 1 byte de aceitação do servidor
        resposta = recv_Tudo(tcp_Socket, 1)
        if not resposta:
            print('\nTimeout: sem resposta do servidor (aceitação do upload).')
            return False
        if resposta[0] != STATUS_OK:
            print('\nServidor recusou o upload.')
            return False

        # aceito: envia 4 bytes com o tamanho do arquivo e depois os blocos
        # durante envio, removemos timeout para não interromper o envio por engano
        tcp_Socket.settimeout(None)
        send_Tudo(tcp_Socket, int_Bytes_BE(tam_Arquivo))

        with open(caminho_local, 'rb') as arquivo:
            restante = tam_Arquivo
            while restante > 0:
                bloco = arquivo.read(BUFFER_SIZE)
                if not bloco:
                    break
                send_Tudo(tcp_Socket, bloco)
                restante -= len(bloco)

        # volta a usar timeout para aguardar o status final
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        final = recv_Tudo(tcp_Socket, 1)
        if not final:
            print('\nTimeout: sem resposta final do servidor após upload.')
            return False
        if final[0] == STATUS_OK:
            print(f'\nUpload concluído com sucesso: {nome_Dest} ({tam_Arquivo} bytes)')
            return True
        else:
            print('\nServidor reportou erro ao processar o upload.')
            return False

    except socket.timeout:
        print('\nTimeout: sem resposta do servidor.')
        return False
    except FileNotFoundError:
        print('\nErro: arquivo local não encontrado (FileNotFoundError).')
        return False
    except socket.error as socket_Erro:
        print(f'\nErro de socket: {socket_Erro}')
        return False
    except Exception as erro:
        print(f'\nErro genérico: {erro}')
        return False
    finally:
        if tcp_Socket:
            try:
                tcp_Socket.close()
            except:
                pass
# 40
def solicitar_Parcial(nome_Arquivo=None, posicao_Inicial=None):
    """
    Solicita o download parcial (a partir de pos_inicial) do arquivo no servidor.

    - Se pos_inicial for None e já existir arquivo local em dest_folder, usa o tamanho atual
      do arquivo local como pos_inicial e envia o MD5 do prefixo local.
    - Se pos_inicial for informado, o cliente calcula o MD5 dos primeiros pos_inicial bytes
      do arquivo local (deve existir), e solicita ao servidor os bytes a partir de pos_inicial.

    Protocolo cliente -> servidor:
      1 byte OP_RESUME (40)
      4 bytes len(nome) + nome
      4 bytes pos_inicial (uint32 BE)
      16 bytes md5 (raw digest)

    Resposta servidor -> cliente:
      1 byte status
      4 bytes tamanho (remaining size or error message length)
      payload
    """
    if not nome_Arquivo:
        print('Nome do arquivo obrigatório.')
        return False

    nome_Seguro = os.path.basename(nome_Arquivo)
    dir_Existe(DIR_IMG_CLIENT)
    caminho_Dest = os.path.join(DIR_IMG_CLIENT, nome_Seguro)

    # se pos_inicial não informado, usar tamanho local (se existir), caso contrário assume 0
    if posicao_Inicial is None:
        if os.path.exists(caminho_Dest):
            posicao_Inicial = os.path.getsize(caminho_Dest)
        else:
            posicao_Inicial = 0

    # precisa ter o prefixo local para calcular MD5 (se pos_inicial > 0)
    if posicao_Inicial > 0:
        if not os.path.exists(caminho_Dest) or os.path.getsize(caminho_Dest) < posicao_Inicial:
            print(os.path.getsize(caminho_Dest))
            print('Erro: arquivo local não possui os bytes necessários para calcular MD5 do prefixo.\n')
            return False
        try:
            md5_local = hashlib.md5()
            lido = 0
            with open(caminho_Dest, 'rb') as arquivo:
                while lido < posicao_Inicial:
                    to_read = min(BUFFER_SIZE, posicao_Inicial - lido)
                    bloco = arquivo.read(to_read)
                    if not bloco:
                        break
                    md5_local.update(bloco)
                    lido += len(bloco)
            md5_digest = md5_local.digest()
        except Exception as erro:
            print(f'Erro ao calcular MD5 local: {erro}')
            return False
    else:
        md5_digest = hashlib.md5(b'').digest()  # MD5 do prefixo vazio

    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((HOST_IP_SERVER, HOST_PORT))

        bytes_Nome = nome_Seguro.encode(CODE_PAGE)
        header = bytes([OP_RESUME]) + int_Bytes_BE(len(bytes_Nome)) + bytes_Nome + int_Bytes_BE(posicao_Inicial) + md5_digest
        send_Tudo(tcp_Socket, header)

        # lê status
        status_Bytes = recv_Tudo(tcp_Socket, 1)
        if not status_Bytes:
            print('Sem resposta do servidor.\n')
            return False
        status = status_Bytes[0]

        # lê 4 bytes tamanho
        size_b = recv_Tudo(tcp_Socket, 4)
        if size_b is None:
            print('Resposta malformada do servidor.\n')
            return False
        tamanho_Dados = bytes_Int_BE(size_b)

        if status != STATUS_OK:
            # payload é mensagem de erro textual (pode ser 0)
            msg = b''
            if tamanho_Dados > 0:
                msg = recv_Tudo(tcp_Socket, tamanho_Dados) or b''
            try:
                print(msg.decode(CODE_PAGE, errors='ignore'))
            except:
                print('Erro do servidor (mensagem binária).\n')
            return False

        # status OK: payload_size = remaining bytes; lê e anexa ao arquivo local
        bytes_Restantes = tamanho_Dados
        # abre arquivo para escrita/append
        if posicao_Inicial == 0:
            arquivo = open(caminho_Dest, 'wb')
        else:
            # se arquivo não existir cria novo; se existir abre para leitura/escrita
            if not os.path.exists(caminho_Dest):
                arquivo = open(caminho_Dest, 'wb')
            else:
                arquivo = open(caminho_Dest, 'r+b')
        try:
            arquivo.seek(posicao_Inicial)
            while bytes_Restantes > 0:
                to_read = min(BUFFER_SIZE, bytes_Restantes)
                bloco = recv_Tudo(tcp_Socket, to_read)
                if bloco is None:
                    print('Conexão encerrada inesperadamente.\n')
                    arquivo.close()
                    return False
                arquivo.write(bloco)
                bytes_Restantes -= len(bloco)
            arquivo.close()
            print(f'\nDownload parcial concluído: {caminho_Dest}')
            return True
        except Exception as erro:
            try:
                arquivo.close()
            except:
                pass
            print(f'Erro ao escrever arquivo: {erro}\n')
            return False

    except socket.timeout:
        print('Timeout: sem resposta do servidor.')
        return False
    except Exception as erro:
        print(f'Erro: {erro}')
        return False
    finally:
        if tcp_Socket:
            try:
                tcp_Socket.close()
            except:
                pass
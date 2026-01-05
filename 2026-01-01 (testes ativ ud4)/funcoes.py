import os
import sys
import socket
import json
from constantes import *

# --- utilitários ---
def dir_existe(caminho):
    if not os.path.exists(caminho):
        os.makedirs(caminho, exist_ok=True)

def safe_join(base, *caminhos):
    """Evita path traversal: ensures returned path is inside base."""
    arq_Teste = os.path.abspath(os.path.join(base, *caminhos))
    base_abs = os.path.abspath(base)
    if not (arq_Teste == base_abs or arq_Teste.startswith(base_abs + os.sep)):
        raise ValueError("Escape da pasta não permitido")
    return arq_Teste

def send_all(socket, data):
    total_enviado = 0
    while total_enviado < len(data):
        enviado = socket.send(data[total_enviado:])
        if enviado == 0:
            raise RuntimeError("Conexão de socket quebrada durante send")
        total_enviado += enviado

def recv_all(socket, n_bytes):
    dados = b''
    while len(dados) < n_bytes:
        bloco = socket.recv(n_bytes - len(dados))
        if not bloco:
            return None
        dados += bloco
    return dados

def pack_uint32_be(n):
    return int(n).to_bytes(4, byteorder='big', signed=False)

def unpack_uint32_be(b):
    return int.from_bytes(b, byteorder='big', signed=False)

# --- servidor (download simples usando cabeçalho: 1 byte status + 4 bytes tamanho) ---
def stream_Arquivo(socket, caminho_Arq):
    """Envia o conteúdo do arquivo em blocos usando send_all."""
    with open(caminho_Arq, 'rb') as arquivo:
        while True:
            bloco = arquivo.read(BUFFER_SIZE)
            if not bloco: break
            send_all(socket, bloco)

# --- funções do servidor (usam EOF como delimitador de fim de arquivo) ---
def unica_Conexao(conexao, cliente):
    """
    Lê 4 bytes (len nome) + nome; responde com:
    1 byte status + 4 bytes tamanho + blocos de dados
    - status == STATUS_OK: blocos de dados = bytes do arquivo
    - status != STATUS_OK: blocos de dados = mensagem de erro (texto)
    """
    try:
        print(f'Conexão de {cliente}')
        # recebe 4 bytes com o tamanho do nome
        tam_Bytes = recv_all(conexao, 4)
        if not tam_Bytes:
            print('Pedido malformado (sem tamanho).')
            return
        tam_Nome = unpack_uint32_be(tam_Bytes)
        nome_Bytes = recv_all(conexao, tam_Nome)
        if nome_Bytes is None:
            print('Pedido malformado (nome incompleto).')
            return
        nome_Arq = nome_Bytes.decode(CODE_PAGE)
        print(f'Requisição de arquivo: {nome_Arq}')

        try:
            caminho = safe_join(DIR_IMG_SERVER, nome_Arq)
        except ValueError:
            msg_erro = 'Caminho inválido'
            dados_Enviados = msg_erro.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_ERRO]) + pack_uint32_be(len(dados_Enviados)) + dados_Enviados)
            return

        if not os.path.isfile(caminho):
            msg_erro = 'Arquivo não encontrado'
            dados_Enviados = msg_erro.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_NOT_FOUND]) + pack_uint32_be(len(dados_Enviados)) + dados_Enviados)
            return

        tam_Arquivo = os.path.getsize(caminho)
        # envia header com status OK e tamanho do arquivo, depois o arquivo em si
        send_all(conexao, bytes([STATUS_OK]) + pack_uint32_be(tam_Arquivo))
        stream_Arquivo(conexao, caminho)
        print(f'Envio concluído: {nome_Arq}')

    except Exception as erro:
        try:
            msg_erro = f'ERRO: {erro}'.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_ERRO]) + pack_uint32_be(len(msg_erro)) + msg_erro)
        except Exception:
            pass
    finally:
        try:
            conexao.close()
        except:
            pass

# --- função do cliente: agora com server_host como parâmetro explícito ---
def solicitar_Arq(server_host, nome, pasta_Dest=None):
    """
    Conecta ao servidor indicado por server_host e solicita o arquivo.
    Agora reaproveita recv_until_eof_and_write para gravar os dados até EOF.
    """
    if pasta_Dest is None: pasta_Dest = DIR_IMG_CLIENT
    dir_existe(pasta_Dest)
    dest_path = os.path.join(pasta_Dest, nome)

    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(TIMEOUT_SOCKET)
        server.connect((server_host, HOST_PORT))

        # envia nome do arquivo (bytes)
        server.send(nome.encode(CODE_PAGE))

        # lê a primeira resposta (pode trazer 'OK' seguido de parte dos dados)
        primeira = server.recv(len(b'OK') + 10)  # tenta ler algo razoável
        if not primeira:
            print('Sem resposta do servidor.')
            return False

        if primeira.startswith(b'OK'):
            resto = primeira[2:]  # pode estar vazio, ou conter dados até EOF
            # usa a função reutilizável para gravar (passando o resto inicial)
            ok = recv_until_eof_and_write(server, dest_path, inicial=resto)
            if ok:
                print(f'Arquivo recebido: {dest_path}')
                return True
            else:
                print('Conexão encerrada inesperadamente.')
                return False
        else:
            # recebeu mensagem de erro (pode ser 'ERRO: ...')
            rest = server.recv(BUFFER_SIZE)
            msg = (primeira + rest).decode(CODE_PAGE, errors='ignore')
            print(msg)
            return False
    except socket.timeout:
        print('Timeout: sem resposta do servidor.')
        return False
    except FileNotFoundError:
        print('Erro ao criar arquivo local.')
        return False
    except socket.error as se:
        print(f'Erro de socket: {se}')
        return False
    except Exception as e:
        print(f'Erro genérico: {e}')
        return False
    finally:
        if server:
            try:
                server.close()
            except:
                pass

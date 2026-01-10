import os
import sys
import socket
import json
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

def send_all(socket, data):
    """Envia todos os bytes de data por meio do socket em um loop. Usa sock.send até que todo o conteúdo seja enviado."""
    total_Enviado = 0
    while total_Enviado < len(data):
        enviado = socket.send(data[total_Enviado:])
        if enviado == 0:
            raise RuntimeError("Conexão de socket quebrada durante send")
        total_Enviado += enviado

def recv_all(socket, n_bytes):
    """lê exatamente n bytes do socket. Faz recv repetidas vezes até completar n bytes; se o socket fechar antes retorna None."""
    dados = b''
    while len(dados) < n_bytes:
        bloco = socket.recv(n_bytes - len(dados))
        if not bloco:
            return None
        dados += bloco
    return dados

def int_Bytes_BE(n):
    return int(n).to_bytes(4, byteorder='big', signed=False)

def bytes_Int_BE(b):
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
        bytes_Tam = recv_all(conexao, 4)
        if not bytes_Tam:
            print('Pedido mal formado (sem tamanho).')
            return
        tam_Nome = bytes_Int_BE(bytes_Tam)
        bytes_Nome = recv_all(conexao, tam_Nome)
        if bytes_Nome is None:
            print('Pedido mal formado (nome incompleto).')
            return
        nome_Arq = bytes_Nome.decode(CODE_PAGE)
        print(f'Requisição de arquivo: {nome_Arq}')

        try:
            caminho = safe_join(DIR_IMG_SERVER, nome_Arq)
        except ValueError:
            msg_erro = 'Caminho inválido'
            dados_Enviados = msg_erro.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
            return

        if not os.path.isfile(caminho):
            msg_erro = 'Arquivo não encontrado'
            dados_Enviados = msg_erro.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_NOT_FOUND]) + int_Bytes_BE(len(dados_Enviados)) + dados_Enviados)
            return

        tam_Arquivo = os.path.getsize(caminho)
        # envia header com status OK e tamanho do arquivo, depois o arquivo em si
        send_all(conexao, bytes([STATUS_OK]) + int_Bytes_BE(tam_Arquivo))
        stream_Arquivo(conexao, caminho)
        print(f'Envio concluído: {nome_Arq}')

    except Exception as erro:
        try:
            msg_erro = f'ERRO: {erro}'.encode(CODE_PAGE)
            send_all(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(msg_erro)) + msg_erro)
        except Exception:
            pass
    finally:
        try:
            conexao.close()
        except:
            pass

# --- funções do cliente: agora com server_host como parâmetro explícito ---
# 10
def solicitar_Arq(server_host, nome, pasta_Dest=None):
    """
    Conecta ao servidor indicado por server_host e solicita o arquivo.

    Conecta a server_host e solicita filename.
    Envia: 4 bytes len(nome) + nome
    Recebe: 1 byte status + 4 bytes tamanho + payload
    """
    if pasta_Dest is None:
        pasta_Dest = DIR_IMG_CLIENT
    dir_Existe(pasta_Dest)
    caminho_Dest = os.path.join(pasta_Dest, nome)

    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((server_host, HOST_PORT))

        # envia nome com 4 bytes de comprimento
        bytes_Nome = nome.encode(CODE_PAGE)
        send_all(tcp_Socket, int_Bytes_BE(len(bytes_Nome)) + bytes_Nome)

        # lê 1 byte de status
        bytes_Status = recv_all(tcp_Socket, 1)
        if not bytes_Status:
            print('Sem resposta do servidor.')
            return False
        status = bytes_Status[0]

        # lê 4 bytes tamanho
        bytes_Tam = recv_all(tcp_Socket, 4)
        if bytes_Tam is None:
            print('Resposta mal formada do servidor.')
            return False
        tam_Dados = bytes_Int_BE(bytes_Tam)

        # lê payload exatamente payload_size bytes (pode ser grande; lê em loop)
        restante = tam_Dados
        dir_Existe(pasta_Dest)
        if status == STATUS_OK:
            with open(caminho_Dest, 'wb') as arquivo:
                while restante > 0:
                    para_Ler = min(BUFFER_SIZE, restante)
                    bloco = recv_all(tcp_Socket, para_Ler)
                    if bloco is None:
                        print('Conexão encerrada inesperadamente.')
                        return False
                    arquivo.write(bloco)
                    restante -= len(bloco)
            print(f'Arquivo recebido: {caminho_Dest}\n{'*' * 30}')
            return True
        else:
            # payload é mensagem de erro/descrição — lê tudo (pode ser 0)
            msg = b''
            if tam_Dados > 0:
                msg = recv_all(tcp_Socket, tam_Dados) or b''
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

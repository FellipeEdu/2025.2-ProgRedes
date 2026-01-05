import os
import sys
import socket
import json
from constantes import *

# --- utilitários ---
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def safe_join(base, *paths):
    """Evita path traversal: ensures returned path is inside base."""
    candidate = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not (candidate == base_abs or candidate.startswith(base_abs + os.sep)):
        raise ValueError("Escape da pasta não permitido")
    return candidate

def send_all(sock, data):
    totalsent = 0
    while totalsent < len(data):
        sent = sock.send(data[totalsent:])
        if sent == 0:
            raise RuntimeError("Conexão de socket quebrada durante send")
        totalsent += sent

def recv_all(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

# --- recv até marcador EOF e grava em arquivo ---
def recv_until_eof_and_write(sock, dest_path):
    """
    Recebe dados do socket e grava em dest_path até encontrar b'EOF'.
    Detecta EOF mesmo que venha fragmentado entre recv calls.
    Retorna True se completou com sucesso, False caso conexão fechada inesperadamente.
    """
    EOF = b'EOF'
    tail_len = len(EOF)  # 3
    tail = b''
    try:
        with open(dest_path, 'wb') as f:
            while True:
                bloco = sock.recv(BUFFER_SIZE)
                if not bloco:
                    # conexão fechada inesperadamente
                    return False
                combined = tail + bloco
                idx = combined.find(EOF)
                if idx != -1:
                    # grava tudo antes do EOF
                    to_write = combined[:idx]
                    if to_write:
                        f.write(to_write)
                    return True
                else:
                    # não encontrou EOF: grava tudo exceto os últimos tail_len bytes
                    if len(combined) <= tail_len:
                        tail = combined
                        continue
                    write_part = combined[:-tail_len]
                    f.write(write_part)
                    tail = combined[-tail_len:]
    except Exception:
        # propaga a exceção para o chamador tratar se necessário
        raise

# --- funções do servidor (usam EOF como delimitador de fim de arquivo) ---
def handle_connection(conn, addr):
    """Lógica de processamento de uma única conexão (download simples)."""
    try:
        print(f'Conexão de {addr}')
        # recebe pedido de nome (até CHUNK_SIZE bytes)
        pedido = conn.recv(BUFFER_SIZE)
        if not pedido:
            print('Recebeu pedido vazio. Encerrando conexão.')
            return
        nome_arquivo = pedido.decode(CODE_PAGE).strip()
        print(f'Recebi pedido para o arquivo: {nome_arquivo}')

        try:
            caminho = safe_join(DIR_IMG_SERVER, nome_arquivo)
        except ValueError:
            print('Pedido tentou escapar da pasta de servidor. Negando.')
            send_all(conn, f'ERRO: Caminho inválido'.encode(CODE_PAGE))
            return

        if not os.path.isfile(caminho):
            print(f'Arquivo não encontrado: {nome_arquivo}')
            msg = f'ERRO: Arquivo não encontrado.'.encode(CODE_PAGE)
            send_all(conn, msg)
            return

        # envia OK e depois o conteúdo em blocos, finalizando com b'EOF'
        print(f'Enviando arquivo: {nome_arquivo}')
        send_all(conn, b'OK')
        with open(caminho, 'rb') as f:
            while True:
                bloco = f.read(BUFFER_SIZE)
                if not bloco:
                    break
                send_all(conn, bloco)
        send_all(conn, b'EOF')
        print(f'Envio concluído: {nome_arquivo}')
    except Exception as e:
        try:
            err = f'ERRO: {e}'.encode(CODE_PAGE)
            send_all(conn, err)
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except:
            pass

# --- função do cliente: agora com server_host como parâmetro explícito ---
def request_file(server_host, filename, dest_folder=None):
    """
    Conecta ao servidor indicado por server_host e solicita o arquivo.
    - server_host: IP ou nome do servidor (string)
    - filename: nome do arquivo pedido (string)
    - dest_folder: pasta destino local (opcional); se None usa constantes.DIR_IMG_CLIENT

    Retorna True se recebeu com sucesso, False caso contrário.
    Exemplo de uso:
        request_file('127.0.0.1', 'arquivo.txt')
    """
    if dest_folder is None:
        dest_folder = DIR_IMG_CLIENT
    ensure_dir(dest_folder)
    dest_path = os.path.join(dest_folder, filename)

    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT_SOCKET)
        s.connect((server_host, HOST_PORT))

        # envia nome do arquivo (bytes)
        s.send(filename.encode(CODE_PAGE))

        # lê a primeira resposta
        primeira = s.recv( len(b'OK') + 10 )  # tenta ler algo razoável
        if not primeira:
            print('Sem resposta do servidor.')
            return False

        if primeira.startswith(b'OK'):
            # resto dos dados pode vir junto com o 'OK'
            resto = primeira[2:]
            # se resto já contém EOF ou dados, escrevemos e chamamos loop para completar
            with open(dest_path, 'wb') as f:
                if resto:
                    # se resto contém EOF
                    idx = resto.find(b'EOF')
                    if idx != -1:
                        # grava até EOF e encerra
                        if idx > 0:
                            f.write(resto[:idx])
                        print(f'Arquivo recebido: {dest_path}')
                        return True
                    else:
                        f.write(resto)
                # agora continuar recebendo até detectar EOF
                tail_len = len(b'EOF')
                tail = b''
                while True:
                    bloco = s.recv(BUFFER_SIZE)
                    if not bloco:
                        print('Conexão encerrada inesperadamente.')
                        return False
                    combined = tail + bloco
                    idx = combined.find(b'EOF')
                    if idx != -1:
                        f.write(combined[:idx])
                        print(f'Arquivo recebido: {dest_path}')
                        return True
                    else:
                        if len(combined) <= tail_len:
                            tail = combined
                            continue
                        write_part = combined[:-tail_len]
                        f.write(write_part)
                        tail = combined[-tail_len:]
        else:
            # recebeu mensagem de erro (pode ser 'ERRO: ...')
            rest = s.recv(BUFFER_SIZE)
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
        if s:
            try:
                s.close()
            except:
                pass

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

def send_Tudo(socket, data):
    """Envia todos os bytes de data por meio do socket em um loop. Usa sock.send até que todo o conteúdo seja enviado."""
    total_Enviado = 0
    while total_Enviado < len(data):
        enviado = socket.send(data[total_Enviado:])
        if enviado == 0:
            raise RuntimeError("Conexão de socket quebrada durante send.")
        total_Enviado += enviado

def recv_Tudo(socket, n_bytes):
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
            send_Tudo(socket, bloco)

# --- funções do servidor (usam EOF como delimitador de fim de arquivo) ---
def unica_Conexao(conexao, cliente):
    """
    Lê uma requisição do cliente e responde com:
      - 1 byte status + 4 bytes tamanho + blocos de dados (payload)
    Suporta duas formas de requisição do cliente:
      A) GET (request de arquivo): cliente envia 4 bytes (len nome) + nome
         -> servidor responde com status + tamanho + blocos do arquivo
      B) LIST (op code 20): cliente envia 1 byte com o código da operação
         -> servidor responde com status + tamanho + payload (JSON com listagem)

    Observação: usa helpers esperados no escopo:
      recv_all, send_all, bytes_Int_BE, int_Bytes_BE, safe_join, stream_Arquivo,
      DIR_IMG_SERVER, CODE_PAGE, STATUS_OK, STATUS_ERRO, STATUS_NOT_FOUND
    """
    try:
        print(f'Conexão de {cliente}')

        # lê 1 byte inicial (pode ser OP_LIST ou o primeiro byte do tamanho do nome)
        primeiro_byte = recv_Tudo(conexao, 1)
        if not primeiro_byte:
            print('ERRO: Pedido mal formado (sem dados iniciais).')
            return

        if primeiro_byte[0] == OP_DOWNLOAD:
            # --- operação GET (recebeu o primeiro byte do tamanho do nome) ---
            # precisamos ler os 3 bytes restantes para completar os 4 bytes do tamanho
            restante_tam = recv_Tudo(conexao, 3)
            if restante_tam is None:
                print('ERRO: Pedido mal formado (tamanho incompleto).')
                return
            bytes_Tam = primeiro_byte + restante_tam  # 4 bytes completos
            tam_Nome = bytes_Int_BE(bytes_Tam)
            bytes_Nome = recv_Tudo(conexao, tam_Nome)
            if bytes_Nome is None:
                print('ERRO: Pedido mal formado (nome incompleto).')
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
            print(f'Envio concluído: {nome_Arq}')

        elif primeiro_byte[0] == OP_LIST:
            # --- operação LIST ---
            try:
                entries = []
                for nome in os.listdir(DIR_IMG_SERVER):
                    caminho = os.path.join(DIR_IMG_SERVER, nome)
                    if os.path.isfile(caminho):
                        tam = os.path.getsize(caminho)
                        entries.append({'nome': nome, 'tamanho': str(tam)})
                payload_text = json.dumps(entries)
                payload = payload_text.encode(CODE_PAGE)
                send_Tudo(conexao, bytes([STATUS_OK]) + int_Bytes_BE(len(payload)) + payload)
                return
            except Exception as e:
                try:
                    msg_Erro = f'ERRO: {e}'.encode(CODE_PAGE)
                    send_Tudo(conexao, bytes([STATUS_ERRO]) + int_Bytes_BE(len(msg_Erro)) + msg_Erro)
                except Exception:
                    pass
                return

        #elif primeiro_byte[0] == OP_UPLOAD:

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
def solicitar_Arq(nome, server_Host=HOST_IP_SERVER, pasta_Dest=DIR_IMG_CLIENT):
    """
    Conecta ao servidor indicado por server_host e solicita o arquivo.

    Conecta a server_host e solicita filename.
    Envia: 4 bytes len(nome) + nome
    Recebe: 1 byte status + 4 bytes tamanho + payload
    """
    #if pasta_Dest is None: pasta_Dest = DIR_IMG_CLIENT
    dir_Existe(pasta_Dest)
    caminho_Dest = os.path.join(pasta_Dest, nome)

    tcp_Socket = None
    try:
        tcp_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_Socket.settimeout(TIMEOUT_SOCKET)
        tcp_Socket.connect((server_Host, HOST_PORT))

        # envia nome com 4 bytes de comprimento
        bytes_Nome = nome.encode(CODE_PAGE)
        send_Tudo(tcp_Socket, int_Bytes_BE(len(bytes_Nome)) + bytes_Nome)

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
        dir_Existe(pasta_Dest)
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
def listar_Arquivos(server_Host=HOST_IP_SERVER):
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
        tcp_Socket.connect((server_Host, HOST_PORT))

        # obtém o código da operação (usa constante se existir, senão 20)
        #OP_LIST = getattr(constantes, 'OP_LIST', 20)
        send_Tudo(tcp_Socket, bytes([OP_LIST]))

        # lê 1 byte de status
        bytes_Status = recv_Tudo(tcp_Socket, 1)
        if not bytes_Status:
            print('Sem resposta do servidor.')
            return None
        status = bytes_Status[0]

        # lê 4 bytes com o tamanho do payload
        bytes_Tam = recv_Tudo(tcp_Socket, 4)
        if bytes_Tam is None:
            print('Resposta malformada do servidor (tamanho ausente).')
            return None
        tam_Dados = bytes_Int_BE(bytes_Tam)

        # lê o payload completo (pode ser 0)
        dados_Enviados = b''
        if tam_Dados > 0:
            dados_Enviados = recv_Tudo(tcp_Socket, tam_Dados)
            if dados_Enviados is None:
                print('Conexão encerrada inesperadamente durante o recebimento do payload.')
                return None

        if status == STATUS_OK:
            # payload esperado em JSON -> decodifica e retorna lista
            try:
                texto = dados_Enviados.decode(CODE_PAGE)
                dados = json.loads(texto)
                return dados
            except Exception as erro:
                print(f'Erro ao decodificar JSON da listagem: {erro}')
                return None
        else:
            # payload é mensagem de erro textual
            try:
                msg = dados_Enviados.decode(CODE_PAGE, errors='ignore')
                print(f'Servidor retornou erro na listagem: {msg}')
            except Exception:
                print('Servidor retornou erro na listagem (mensagem binária).')
            return None

    except socket.timeout:
        print('Timeout: sem resposta do servidor.')
        return None
    except socket.error as erro_Socket:
        print(f'Erro de socket: {erro_Socket}')
        return None
    except Exception as erro:
        print(f'Erro genérico: {erro}')
        return None
    finally:
        if tcp_Socket:
            try:
                tcp_Socket.close()
            except:
                pass
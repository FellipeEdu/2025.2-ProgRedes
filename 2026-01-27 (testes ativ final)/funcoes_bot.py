import struct, socket, json

# ----------------------------------------------------------------------
def startBot() -> str:
    """
    Retorna mensagem de boas vindas do bot.
    """
    return (
        "Bem-vindo ao BOT SHOW METRICS CNAT!\n\n"
        "Este é um bot para consultar métricas de performance dos dispositivos conectados.\n\n"
        "/? → Exibe mensagem de ajuda."
        )

def mostrarAgentes(dictAgentes) -> str:
    """
    Retorna os agentes conectados.
    """
    return (
        "Agentes conectados:\n" + ("\n".join(dictAgentes.keys()) if dictAgentes else "Nenhum")
    )
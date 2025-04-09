# client/main.py
import os
import sys
import time
import signal
import argparse
from managers.client_manager import ClientManager
from utils.logger import setup_logger
from config import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
def parse_arguments():
    parser = argparse.ArgumentParser(description='Cliente de Monitoramento')
    parser.add_argument('--host', default=DEFAULT_SERVER_HOST, 
                        help=f'Endereço IP do servidor (padrão: {DEFAULT_SERVER_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, 
                        help=f'Porta do servidor (padrão: {DEFAULT_SERVER_PORT})')
    return parser.parse_args()
def setup_signal_handlers(client):
    def signal_handler(sig, frame):
        logger.info("Sinal de interrupção recebido, encerrando cliente...")
        client.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    global logger
    logger = setup_logger()
    args = parse_arguments()
    logger.info("Iniciando cliente de monitoramento")
    logger.info(f"Configurado para conectar em {args.host}:{args.port}")
    try:
        client = ClientManager(args.host, args.port)
        setup_signal_handlers(client)
        logger.info(f"Tentando conectar ao servidor {args.host}:{args.port}")
        success = client.start()
        if success:
            logger.info("Cliente conectado e iniciado com sucesso")
        else:
            logger.warning("Cliente iniciado, mas não foi possível conectar ao servidor")
            logger.info("Tentativas de reconexão serão feitas automaticamente")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupção de teclado detectada, encerrando cliente...")
    except Exception as e:
        logger.error(f"Erro não tratado: {str(e)}", exc_info=True)
    finally:
        try:
            client.stop()
        except:
            pass
        logger.info("Cliente encerrado")
if __name__ == "__main__":
    main()

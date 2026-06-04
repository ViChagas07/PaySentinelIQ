# ============================================================
# PaySentinelIQ — Application Entry Point (Repository Root Proxy)
# ============================================================
# Este arquivo é um proxy para o app real em Back-end/app/main.py.
# Ele existe na raiz do repositório para que o Railpack (Railway)
# consiga detectar Python e construir o projeto corretamente,
# mesmo sem configurar "Root Directory = Back-end/" no dashboard.
#
# Quando o Root Directory for configurado, este arquivo não será
# mais necessário e pode ser removido.
# ============================================================

import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona Back-end/ ao path para conseguir importar o app real
_backend_dir = os.path.join(os.path.dirname(__file__), "Back-end")
sys.path.insert(0, _backend_dir)

# Importa a factory do app real
logger.info("Importing PaySentinelIQ app from %s", _backend_dir)
from app.main import create_app

# Cria a instância do app (o uvicorn usará esta variável 'app')
app = create_app()
logger.info("PaySentinelIQ app created successfully")

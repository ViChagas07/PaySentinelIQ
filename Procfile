# 🚀 PaySentinelIQ — Procfile
# Compatível com Heroku, Render, Railway, Fly.io

# API Principal (uvicorn com factory)
web: python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --workers 1 --ws-ping-interval 30 --ws-ping-timeout 10 --ws-max-size 1048576

# Workers (descomente para usar em plataformas que suportam multiple processes)
# worker-audit: python -m app.workers.audit_worker
# worker-notification: python -m app.workers.notification_worker
# worker-email: python -m app.workers.email_worker
# worker-scheduler: python -m app.workers.scheduler

# Para rodar tudo em um processo único (Koyeb Free Tier):
# web: python -m app.run_all
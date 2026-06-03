# ============================================================
# PaySentinelIQ — Application Entry Point
# Run with: python -m app.main or uvicorn app.main:create_app --factory
# ============================================================

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.shared.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

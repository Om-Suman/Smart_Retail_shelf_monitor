from __future__ import annotations

from src.app_factory import create_app

app = create_app()


# --------------------------------------------------------
# Run
# --------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    from src.core.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )

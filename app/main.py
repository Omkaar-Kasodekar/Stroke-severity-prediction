from fastapi import FastAPI

from .db import init_db
from .routes import router as api_router


app = FastAPI(
    title="Stroke Severity Clinical Decision Support System",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    # Initialize database tables
    init_db()


app.include_router(api_router)


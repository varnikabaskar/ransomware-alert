from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.responses import RedirectResponse

from server.app.routers.agent import router as agent_router
from server.app.routers.alerts import router as alerts_router
from server.app.routers.health import router as health_router
from server.app.routers.train import router as train_router

app = FastAPI(title="R-GUARD Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(agent_router)
app.include_router(alerts_router)
app.include_router(train_router)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/dashboard", StaticFiles(directory=str(STATIC_DIR), html=True), name="dashboard")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")

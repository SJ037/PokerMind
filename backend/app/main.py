from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.analysis import router as analysis_router
from backend.app.api.opponents import router as opponents_router
from backend.app.api.ranges import router as ranges_router

app = FastAPI(title="PokerMind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(opponents_router, prefix="/api", tags=["opponents"])
app.include_router(ranges_router, prefix="/api", tags=["ranges"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

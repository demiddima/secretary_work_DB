from fastapi import APIRouter

router = APIRouter(
    tags=["health"]
)

@router.get("/", tags=["health"])
async def root():
    return {"status": "ok"}

@router.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}

@router.get("/panic")
async def panic():
    raise RuntimeError("🔥 Это тестовый RuntimeError")
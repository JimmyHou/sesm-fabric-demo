from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import asyncio

from memory_store import store, MemoryItem


class WriteMemoryRequest(BaseModel):
    content: str
    ttl_seconds: int = 60


app = FastAPI(title="SESM Fabric", version="0.1.0")

# Allow browser UI to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React UI from /static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/memory/write", response_model=MemoryItem)
async def write_memory(payload: WriteMemoryRequest):
    """
    Write an episodic event.
    If content repeats, it reinforces and can promote to knowledge.
    """
    item = store.write_event(
        content=payload.content,
        ttl_seconds=payload.ttl_seconds,
    )
    return item


@app.get("/memory/episodic", response_model=List[MemoryItem])
async def get_episodic():
    return store.list_episodic()


@app.get("/memory/knowledge", response_model=List[MemoryItem])
async def get_knowledge():
    return store.list_knowledge()


@app.get("/memory/all", response_model=List[MemoryItem])
async def get_all():
    return store.list_all()


async def cleanup_loop():
    """
    Periodically clean up expired episodic memories.
    This simulates TTL decay.
    """
    while True:
        store.cleanup_expired()
        await asyncio.sleep(5)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(cleanup_loop())

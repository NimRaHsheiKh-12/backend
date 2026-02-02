#!/usr/bin/env python3
"""Minimal FastAPI test to verify server stays running"""
from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()


class Message(BaseModel):
    text: str


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/test")
async def test_endpoint(msg: Message = Body(...)):
    return {"received": msg.text, "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

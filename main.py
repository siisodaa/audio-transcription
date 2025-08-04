from fastapi import FastAPI
from routes.transcription_routes import router as transcription_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config.db import connect

app = FastAPI()
app.include_router(transcription_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    app.state.db = connect()

if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port = 8000, reload=True)
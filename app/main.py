from fastapi import FastAPI
from app.api.routes import auth, calendar 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OnmyoCalendar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "https://onmyocalendar-be-api.onrender.com",
        "https://onmyocalendar.github.io"
    ],
    allow_credentials=True,      
    allow_methods=["*"],         
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"]) 

@app.get("/")
def keep_alive():
    return {"status": "Server is awake!"}
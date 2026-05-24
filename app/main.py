from fastapi import FastAPI
from app.api.routes import auth, calendar # Import thêm calendar
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OnmyoCalendar")

app.add_middleware(
    CORSMiddleware,
    # BẮT BUỘC: Ghi chính xác địa chỉ Frontend của bạn (Không có dấu / ở cuối)
    # LƯU Ý: Tuyệt đối không dùng ["*"] ở đây khi đã bật allow_credentials=True
    allow_origins=[
        "http://localhost:5173", # Nếu bạn dùng Vite
        "http://localhost:3000", # Nếu bạn dùng Create React App
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,      # BẮT BUỘC TRUE: Để cho phép nhận Cookie từ Frontend
    allow_methods=["*"],         # Cho phép tất cả các method (GET, POST, OPTIONS...)
    allow_headers=["*"],
)
# Đăng ký các router
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"]) 

@app.get("/")
def root():
    return {"message": "Backend FastAPI đang chạy ổn định!"}
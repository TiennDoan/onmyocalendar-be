from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import List

router = APIRouter()

# --- Schema ---
class TokenPayload(BaseModel):
    access_token: str
    refresh_token: str

class BossSchedulePayload(BaseModel):
    start_date: str         
    duration_months: int    

    boss_colors: List[str]

# --- API Test (Đã sửa lỗi datetime) ---
@router.post("/create-test-event")
def create_test_event(payload: TokenPayload):
    try:
        creds = Credentials(
            token=payload.access_token,
            refresh_token=payload.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        service = build('calendar', 'v3', credentials=creds)

        # Ở đây chỉ gọi thẳng datetime.utcnow() và timedelta()
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        event = {
            'summary': '🚀 Lịch Test từ Dự Án FastAPI',
            'location': 'Ho Chi Minh City, Vietnam',
            'start': {'dateTime': start_time.isoformat() + 'Z', 'timeZone': 'UTC'},
            'end': {'dateTime': end_time.isoformat() + 'Z', 'timeZone': 'UTC'},
        }

        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return {"message": "Tạo sự kiện thành công!", "event_link": event_result.get('htmlLink')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


# --- API Tạo Lịch Boss & Buff ---
@router.post("/create-boss-schedule")
def create_boss_schedule(payload: BossSchedulePayload, request: Request):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Bạn chưa đăng nhập Google")
    
    try:
        # Validate nhanh: Đảm bảo Frontend gửi đủ 7 màu cho 7 ngày
        if len(payload.boss_colors) != 7:
            payload.boss_colors = ["1", "1", "1", "1", "1", "1", "1"]

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        service = build('calendar', 'v3', credentials=creds)

        # 1. Tạo lịch phụ
        new_calendar = {
            'summary': f'OnmyoCalendar',
            'timeZone': 'Asia/Ho_Chi_Minh'
        }
        created_calendar = service.calendars().insert(body=new_calendar).execute()
        target_calendar_id = created_calendar['id']

        # 2. Chuẩn bị dữ liệu
        BOSSES = ["GEISHA", "ULTRA SHINKIROU", "OBOROGURUMA", "ULTRA ODOKURO", "ULTRA NAMAZU", "ULTRA TSUCHIGUMO", "NIGHTLY ARAMITAMA"]
        BUFFS = ["STRONG FIRE", "RAGING WIND", "FIGHTING SOUL", "DASH", "SKILLFUL", "FRAGILE"]
        ANCHOR_DATE = datetime.strptime("2026-05-13", "%Y-%m-%d")

        HEX_TO_GOOGLE_ID = {
            "#7986cb": "1",  # Lavender
            "#33b679": "2",  # Sage
            "#8e24aa": "3",  # Grape
            "#e67c73": "4",  # Flamingo
            "#f6c026": "5",  # Banana
            "#f5511d": "6",  # Tangerine
            "#039be5": "7",  # Peacock
            "#616161": "8",  # Graphite
            "#3f51b5": "9",  # Blueberry
            "#0b8043": "10", # Basil
            "#d50000": "11"  # Tomato
        }
        start_date = datetime.strptime(payload.start_date, "%Y-%m-%d")
        total_days = payload.duration_months * 30 
        success_count = 0 

        def batch_callback(request_id, response, exception):
            nonlocal success_count
            if exception is None:
                success_count += 1

        batch = service.new_batch_http_request(callback=batch_callback)

        # 3. Vòng lặp
        for i in range(total_days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # ==========================================
            # LỊCH BUỔI TỐI (Thuộc về chu kỳ của ngày hiện tại)
            # ==========================================
            evening_weekday = current_date.weekday()
            evening_days_from_anchor = (current_date - ANCHOR_DATE).days
            
            evening_boss = BOSSES[evening_weekday]
            evening_buff = BUFFS[evening_days_from_anchor % len(BUFFS)]
            evening_hex = payload.boss_colors[evening_weekday].lower()
            evening_color = HEX_TO_GOOGLE_ID.get(evening_hex, "9")

            if evening_weekday in [0, 2, 6]:
                evening_summary = f'{evening_boss}'
            else:
                evening_summary = f'[{evening_buff}] {evening_boss}'

            event_evening = {
                'summary': f'{evening_summary}',
                'colorId': evening_color,
                'start': {'dateTime': f'{date_str}T18:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
                'end': {'dateTime': f'{date_str}T21:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'}
            }
            
            # ==========================================
            # LỊCH BUỔI SÁNG (Thuộc về chu kỳ của ngày hôm trước)
            # ==========================================
            prev_date = current_date - timedelta(days=1)
            morning_weekday = prev_date.weekday()
            morning_days_from_anchor = (prev_date - ANCHOR_DATE).days
            
            morning_boss = BOSSES[morning_weekday]
            morning_buff = BUFFS[morning_days_from_anchor % len(BUFFS)]
            morning_hex = payload.boss_colors[morning_weekday].lower()
            morning_color = HEX_TO_GOOGLE_ID.get(morning_hex, "9")

            if morning_weekday in [0, 2, 6]:
                morning_summary = f'{morning_boss}'
            else:
                morning_summary = f'[{morning_buff}] {morning_boss}'

            event_morning = {
                'summary': f'{morning_summary}',
                'colorId': morning_color,
                'start': {'dateTime': f'{date_str}T07:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
                'end': {'dateTime': f'{date_str}T10:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'}
            }

            # Đẩy cả 2 sự kiện vào lô (batch) để gửi lên Google
            batch.add(service.events().insert(calendarId=target_calendar_id, body=event_morning))
            batch.add(service.events().insert(calendarId=target_calendar_id, body=event_evening))

        batch.execute()

        # (Tùy chọn) Thêm một câu return JSON ở cuối để Frontend nhận được data sau khi tạo xong
        return

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
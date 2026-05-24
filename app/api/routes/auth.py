import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from app.core.config import settings
import uuid # 
import json

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

router = APIRouter()

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
    }
}

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]


session_cache = {}

@router.get("/login")
def login():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    

    custom_state = str(uuid.uuid4())
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=custom_state 
    )
    

    session_cache[state] = flow.code_verifier

    return RedirectResponse(url=authorization_url)

@router.get("/callback")
def callback(request: Request):

    state = request.query_params.get("state")
    
    code_verifier = session_cache.get(state)
    
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Không tìm thấy phiên đăng nhập. Vui lòng thử lại.")

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    flow.code_verifier = code_verifier
    
    del session_cache[state]
    
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    token_data = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token or ""
    }

    token_json = json.dumps(token_data)
    html_content = f"""
    <html>
        <head><title>Đăng nhập thành công</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h3 style="color: #475569;">Đang kết nối lại ứng dụng...</h3>
            <script>
                try {{
                    if (window.opener) {{
                        window.opener.postMessage({token_json}, "https://onmyocalendar.github.io");
                        window.close();
                    }} else {{
                        document.body.innerHTML += "<p style='color:red;'>Lỗi: Trình duyệt chặn giao tiếp.</p>";
                    }}
                }} catch(e) {{
                    console.error(e);
                }}
            </script>
        </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

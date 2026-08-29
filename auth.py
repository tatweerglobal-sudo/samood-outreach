import secrets
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
import database

# ذاكرة الجلسات النشطة في السيرفر
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 86400 * 7 # جلسة صالحة لمدة 7 أيام

def create_session(username: str, display_name: str) -> str:
    token = secrets.token_hex(32)
    ACTIVE_SESSIONS[token] = {
        "username": username,
        "display_name": display_name,
        "created_at": time.time()
    }
    return token

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    if token not in ACTIVE_SESSIONS:
        return None
    session = ACTIVE_SESSIONS[token]
    if time.time() - session["created_at"] > SESSION_TTL_SECONDS:
        del ACTIVE_SESSIONS[token]
        return None
    return session

def destroy_session(token: str):
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]

cookie_sec = APIKeyCookie(name="samood_session", auto_error=False)
bearer_sec = HTTPBearer(auto_error=False)

async def get_current_admin(
    cookie_token: Optional[str] = Depends(cookie_sec),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_sec)
) -> Dict[str, Any]:
    token = cookie_token
    if not token and bearer_token:
        token = bearer_token.credentials
        
    if not token:
        # السماح بالقراءة السلسة إذا كانت الطلبات محلية، أما على السيرفر الأونلاين فتُفرض الحماية
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يلزم تسجيل الدخول أولاً للوصول للسيرفر السحابي لشركة صمود"
        )
        
    session = verify_token(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة العمل انتهت أو غير صالحة. يرجى إعادة تسجيل الدخول"
        )
    return session

import secrets
import hashlib
import base64
import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from urllib.parse import urlencode
import logging

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置信息
CONFIG = {
    'MAL_CLIENT_ID': '',
    'MAL_CLIENT_SECRET': '',
    'ANILIST_CLIENT_ID': '',
    'ANILIST_CLIENT_SECRET': '',
    'REDIRECT_URI': 'https://auth.amoe.moe/callback',
    'DD_APPID': '',
    'DD_SK': ''
}

# 存储验证码
code_verifiers = {}

def get_new_code_verifier() -> str:
    """生成新的验证码"""
    token = secrets.token_urlsafe(100)
    return token[:128]

@app.get("/")
async def home():
    """主页"""
    return HTMLResponse(content="""
        Welcome to OAuth example! 
        <br><a href="/login/mal">Login with MAL</a>
        <br><a href="/login/anilist">Login with AniList</a>
    """)

@app.get("/login/mal")
async def mal_login():
    """MAL登录"""
    code_verifier = get_new_code_verifier()
    code_verifiers['mal'] = code_verifier
    
    auth_url = f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={CONFIG["MAL_CLIENT_ID"]}&code_challenge={code_verifier}'
    return RedirectResponse(url=auth_url)

@app.get("/login/anilist")
async def anilist_login():
    """AniList登录"""
    params = {
        'client_id': CONFIG['ANILIST_CLIENT_ID'],
        'redirect_uri': CONFIG['REDIRECT_URI'],
        'response_type': 'code'
    }
    
    auth_url = f'https://anilist.co/api/v2/oauth/authorize?{urlencode(params)}'
    logging.info(f"AniList auth URL: {auth_url}")
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def auth_callback(
    code: str = Query(None),
    state: str = Query(None)
):
    """处理OAuth回调"""
    if not code:
        return HTMLResponse(content='Authorization failed.', status_code=400)
    
    try:
        # MAL回调处理
        if code_verifiers.get('mal'):
            code_verifier = code_verifiers.pop('mal')  # 获取并立即删除
            
            payload = {
                'client_id': CONFIG['MAL_CLIENT_ID'],
                'client_secret': CONFIG['MAL_CLIENT_SECRET'],
                'code': code,
                'code_verifier': code_verifier,
                'grant_type': 'authorization_code'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://myanimelist.net/v1/oauth2/token',
                    data=payload
                )
                
                if response.status_code != 200:
                    return HTMLResponse(content='Failed to obtain access token.', status_code=400)
                
                token_data = response.json()
                return HTMLResponse(content=f'Access token obtained: {token_data["access_token"]}')
                
        # AniList回调处理
        else:
            payload = {
                'grant_type': 'authorization_code',
                'client_id': CONFIG['ANILIST_CLIENT_ID'],
                'client_secret': CONFIG['ANILIST_CLIENT_SECRET'],
                'redirect_uri': CONFIG['REDIRECT_URI'],
                'code': code
            }
            
            logging.info(f"AniList token request payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://anilist.co/api/v2/oauth/token',
                    json=payload,  # 使用 json 而不是 data
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                )
                
                if response.status_code != 200:
                    logging.error(f"AniList token request failed: {response.text}")
                    return HTMLResponse(content=f'Failed to obtain access token: {response.text}', status_code=400)
                
                token_data = response.json()
                return HTMLResponse(content=f'Access token obtained: {token_data["access_token"]}')
                
    except Exception as e:
        logging.error(f"认证错误: {str(e)}")
        return HTMLResponse(content='Authorization failed.', status_code=400)

def generate_signature(timestamp: int, path: str) -> str:
    """
    生成签名
    """
    # 按顺序拼接字符串
    raw_string = f"{CONFIG['DD_APPID']}{timestamp}{path}{CONFIG['DD_SK']}"
    
    # SHA256哈希
    sha256_hash = hashlib.sha256(raw_string.encode()).digest()
    
    # Base64编码
    signature = base64.b64encode(sha256_hash).decode()
    
    return signature

@app.post("/auth")
async def get_auth_headers(request: Request):
    """
    生成认证头信息
    """
    try:
        # 获取请求体数据
        data = await request.json()
        path = data.get("path", "").lower()
        
        if not path:
            raise HTTPException(status_code=400, detail="路径不能为空")
            
        # 获取当前时间戳
        timestamp = int(time.time())
        
        # 生成签名
        signature = generate_signature(timestamp, path)
        
        # 返回认证头信息
        return {
            "headers": {
                "X-AppId": CONFIG['DD_APPID'],
                "X-Timestamp": str(timestamp),
                "X-Signature": signature
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
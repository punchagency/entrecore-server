import httpx
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthValidator:
    def __init__(self, auth_service_url: str = "http://auth_service:8000"):
        self.auth_service_url = auth_service_url
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await self.security(request)
        token = credentials.credentials
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_service_url}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials"
                )
            
            return response.json()
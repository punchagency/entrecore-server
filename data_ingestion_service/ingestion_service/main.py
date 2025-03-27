from fastapi import FastAPI, Depends, HTTPException
import os
from datetime import datetime
from .middleware.auth import AuthValidator

app = FastAPI(title="Data Ingestion Service",
              description="Service for connecting to data sources, extracting data, profiling it, and storing metadata",
              version="0.1.0")
auth_validator = AuthValidator()

@app.get("/api/v1")
async def root():
    return {"message": "Data Ingestion Service API", "status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/version")
async def version():
    return {"version": app.version}

@app.get("/api/v1/protected-endpoint")
async def protected_endpoint(user_data = Depends(auth_validator)):
    return {"message": "This is a protected endpoint", "user": user_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

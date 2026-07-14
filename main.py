from onboard_agent import config
from fastapi import FastAPI
from onboard_agent.api.endpoints import router
from onboard_agent.api.middleware import setup_middleware

import uvicorn

app = FastAPI(title="onboard-agent")
app.include_router(router)
setup_middleware(app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
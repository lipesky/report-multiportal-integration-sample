from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from src.routers.report_router import router as report_router
from src.routers.user_router import router as user_router
from src.model.settings import Settings

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

app = FastAPI(
    title="Sample multiportal Report Service",
)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(user_router)

@app.get('/')
async def rootRoute():
    return Response('multiportal-report-api', status_code=200)

@app.get('/healthcheck')
async def healthcheck():
    return Response(status_code=200)

if __name__ == '__main__':
    from uvicorn import run
    import os
    run(
        'main:app',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '8000' if Settings().environment == 'DEV' else '80')),
        reload=Settings().environment == 'DEV',
        #root_path='/trip-service-api'
    )
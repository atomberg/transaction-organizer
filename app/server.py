import uvicorn
import logging
from .blueprints.transactions import router as transactions_router
from fastapi import FastAPI, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .dependencies import get_db

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(transactions_router, prefix='/transactions', dependencies=[Depends(get_db)])


@app.get('/')
async def main():
    return {"message": "Hello Bigger Applications!"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"{request}: {exc_str}")
    logging.error(f"exc.body: {exc.body}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

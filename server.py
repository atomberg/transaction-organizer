import uvicorn
import logging
from app.routes import transactions, persons
from fastapi import FastAPI, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.dependencies import get_db, get_settings, Settings

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(
    transactions.router, prefix='/transactions', dependencies=[Depends(get_db)], tags=['transactions']
)
app.include_router(persons.router, prefix='/persons', dependencies=[Depends(get_db)], tags=['persons'])
# app.include_router(reports.router, prefix='/reports', dependencies=[Depends(get_db)], tags=['reports'])


@app.get('/', dependencies=[Depends(get_settings)])
async def main(settings: Settings = Depends(get_settings)):
    return {
        "message": "Hello Bigger Applications!",
        "db_uri": settings.sqlalchemy_database_uri,
        "tax_year": settings.tax_year,
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"{request}: {exc_str}")
    logging.error(f"exc.body: {exc.body}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import uvicorn
from app.runserver import runserver

if __name__ == "__main__":
    uvicorn.run(
        runserver,
        ws='auto',
        interface='asgi3',
        loop='asyncio',
        lifespan='off',
        host='10.218.227.134',
        port=8500,
        log_level='debug',
        timeout_keep_alive=1000
    )


from fastapi.responses import JSONResponse


def success(message: str, data=None, **extra) -> dict:
    response = {"status": "success", "message": message}
    if data is not None:
        response["data"] = data
    response.update(extra)
    return response


def error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        {"status": "error", "message": message},
        status_code=status_code,
    )

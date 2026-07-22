from fastapi.responses import JSONResponse


def success_response(
    data=None,
    message="Success",
):

    return JSONResponse(

        status_code=200,

        content={

            "success": True,

            "message": message,

            "data": data,
        },
    )
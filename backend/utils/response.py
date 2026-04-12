def create_response(data, message="Success"):
    return {"status": "success", "message": message, "data": data}


def create_error(message="Something went wrong"):
    return {"status": "error", "message": message}

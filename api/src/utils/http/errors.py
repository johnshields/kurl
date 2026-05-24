"""
Custom errors
Custom API error for returning structured error responses.
"""


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str, code: str = "INTERNAL_ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(detail)

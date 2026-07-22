"""Domain exception base classes.

Services raise these instead of building HTTPException themselves or
requiring every router endpoint to carry its own try/except. Handlers
registered in handlers.py catch the base classes once, globally, so any
new subclass raised anywhere is mapped to the right HTTP status
automatically — no router boilerplate, and no way to forget the mapping.
"""


class NotFoundError(Exception):
    """A requested resource doesn't exist -> 404."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(message)


class DomainError(Exception):
    """A business-rule violation (bad input, invalid state transition,
    etc.) that should surface as 400 Bad Request, not crash."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

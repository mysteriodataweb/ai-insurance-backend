class NotFoundError(Exception):
    """Resource does not exist (HTTP 404)."""


class ConflictError(Exception):
    """Action is not allowed in the current state of the claim (HTTP 409)."""


class LLMError(Exception):
    """The AI provider failed or returned unusable output (HTTP 502)."""

"""Shared HTTP client factory with correct SSL verification for Windows."""
import httpx
import certifi


def make_client(**kwargs) -> httpx.AsyncClient:
    """Returns an AsyncClient with certifi CA bundle for SSL verification."""
    return httpx.AsyncClient(verify=certifi.where(), **kwargs)

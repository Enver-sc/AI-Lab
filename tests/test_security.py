import socket
import pytest
from app.services.url_security import validate_provider_url

def resolver(ip):
    return lambda *args,**kwargs:[(socket.AF_INET,socket.SOCK_STREAM,6,"",(ip,443))]

def test_ssrf_blocks_private():
    with pytest.raises(ValueError):
        validate_provider_url("https://example.test",resolver=resolver("10.0.0.1"))

def test_ssrf_allows_public():
    assert validate_provider_url("https://example.test/v1",resolver=resolver("93.184.216.34"))=="https://example.test/v1"

def test_localhost_only_for_ollama():
    with pytest.raises(ValueError):
        validate_provider_url("http://localhost:11434")
    assert validate_provider_url("http://localhost:11434",True,resolver=resolver("127.0.0.1"))


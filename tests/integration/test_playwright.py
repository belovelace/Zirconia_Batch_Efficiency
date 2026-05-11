import pytest
import requests


@pytest.mark.integration
def test_readiness_endpoint():
    url = "http://localhost:8000/health/ready"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert "ready" in body

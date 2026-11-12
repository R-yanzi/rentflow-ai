"""健康检查接口测试。"""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_check() -> None:
    """健康检查接口应该返回稳定的结构化响应。"""
    test_settings = Settings(
        name="RentFlow AI Test API",
        version="test",
        debug=True,
    )
    application = create_app(test_settings)

    with TestClient(application) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "RentFlow AI Test API",
        "version": "test",
    }

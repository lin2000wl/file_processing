import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """主应用测试"""

    def test_health_check(self, test_client: TestClient):
        """测试健康检查接口"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_redirect(self, test_client: TestClient):
        """测试根路径重定向"""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_cors_headers(self, test_client: TestClient):
        """测试CORS头部"""
        response = test_client.options("/health")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_api_prefix(self, test_client: TestClient):
        """测试API前缀路由"""
        response = test_client.get("/api/v1/files/")
        # 应该返回文件列表，即使为空
        assert response.status_code == 200


class TestErrorHandling:
    """错误处理测试"""

    def test_404_error(self, test_client: TestClient):
        """测试404错误处理"""
        response = test_client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client: TestClient):
        """测试方法不允许错误"""
        response = test_client.post("/health")
        assert response.status_code == 405 
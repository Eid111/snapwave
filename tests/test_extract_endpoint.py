import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app


class ExtractEndpointTests(unittest.TestCase):
    def test_extract_endpoint_awaits_service_result(self):
        response_data = {
            "host": "example.com",
            "title": "Sample video",
            "author": "Channel",
            "duration": 12,
            "date": "Available now",
            "thumbnail": "/assets/favicon.svg",
            "target_url": "https://example.com/video",
            "referer": "https://example.com/video",
            "formats": [],
        }
        password = "deployment-smoke-test-password"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch("backend.main.ADMIN_PASSWORD_ENV", password), patch(
                "backend.core.site_settings.ADMIN_PASSWORD_ENV", password
            ), patch("backend.core.site_settings.CONFIG_FILE", config_file):
                with TestClient(app) as client, patch(
                    "backend.api.v1.endpoints.extract.YtDlpService.extract_info",
                    new_callable=AsyncMock,
                    return_value=response_data,
                ) as extract_info:
                    response = client.post(
                        "/api/v1/extract",
                        json={"url": "https://8.8.8.8/video"},
                    )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["title"], "Sample video")
        extract_info.assert_awaited_once_with("https://8.8.8.8/video")


if __name__ == "__main__":
    unittest.main()

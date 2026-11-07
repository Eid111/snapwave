import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.core import site_settings
from backend.core.passwords import verify_password
from backend.main import app, lifespan


class SiteSettingsPasswordTests(unittest.TestCase):
    def test_initialization_requires_password(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", ""
            ):
                with self.assertRaisesRegex(RuntimeError, "ADMIN_PASSWORD"):
                    site_settings.load_settings()

    def test_initialization_rejects_short_password(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", "too-short"
            ):
                with self.assertRaisesRegex(RuntimeError, "at least 16 characters"):
                    site_settings.load_settings()

    def test_initialization_hashes_configured_password(self):
        password = "a-unique-admin-passphrase"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", password
            ):
                settings = site_settings.load_settings()

        self.assertNotEqual(settings["admin_password_hash"], password)
        self.assertTrue(verify_password(password, settings["admin_password_hash"]))

    def test_known_default_hash_is_migrated_to_configured_password(self):
        configured_password = "a-unique-admin-passphrase"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            config_file.write_text(
                '{"admin_password_hash": "'
                + site_settings.hash_password("changeme_secure_2026")
                + '"}',
                encoding="utf-8",
            )
            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", configured_password
            ):
                settings = site_settings.load_settings()

        self.assertTrue(
            verify_password(configured_password, settings["admin_password_hash"])
        )
        self.assertFalse(
            verify_password("changeme_secure_2026", settings["admin_password_hash"])
        )

    def test_existing_password_hash_does_not_require_environment_variable(self):
        password = "a-unique-admin-passphrase"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", password
            ):
                initial_settings = site_settings.load_settings()

            with patch.object(site_settings, "CONFIG_FILE", config_file), patch.object(
                site_settings, "ADMIN_PASSWORD_ENV", ""
            ):
                settings = site_settings.load_settings()

        self.assertEqual(
            settings["admin_password_hash"], initial_settings["admin_password_hash"]
        )

    def test_application_startup_rejects_missing_password(self):
        async def start_application():
            async with lifespan(app):
                pass

        with patch("backend.main.ADMIN_PASSWORD_ENV", ""):
            with self.assertRaisesRegex(RuntimeError, "at least 16 characters"):
                asyncio.run(start_application())

    def test_application_startup_accepts_strong_password(self):
        async def start_application():
            async with lifespan(app):
                pass

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "site_config.json"
            with patch("backend.main.ADMIN_PASSWORD_ENV", "a-unique-admin-passphrase"), patch(
                "backend.core.site_settings.ADMIN_PASSWORD_ENV",
                "a-unique-admin-passphrase",
            ), patch("backend.core.site_settings.CONFIG_FILE", config_file):
                asyncio.run(start_application())


if __name__ == "__main__":
    unittest.main()

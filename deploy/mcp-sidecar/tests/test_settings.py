import pytest

from personal_mcp.settings import Settings


def test_settings_reject_short_assertion_secret(monkeypatch):
	values = {
		"FRAPPE_BASE_URL": "http://personal:8000",
		"FRAPPE_PUBLIC_URL": "https://pip.lly.info",
		"FRAPPE_SITE": "pip.lly.info",
		"MCP_PUBLIC_URL": "https://pip.lly.info/mcp",
		"MCP_ASSERTION_SECRET": "short",
		"MCP_ALLOWED_HOSTS": "pip.lly.info,pip.lly.info:*",
		"MCP_ALLOWED_ORIGINS": "https://pip.lly.info",
	}
	for name, value in values.items():
		monkeypatch.setenv(name, value)

	with pytest.raises(RuntimeError, match="at least 32"):
		Settings.from_environment()

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import frappe
import jwt
from frappe.tests import IntegrationTestCase

from personal.health import sidecar_api

TEST_SECRET = "test-only-mcp-assertion-secret-that-is-long-enough"


class TestSidecarAPI(IntegrationTestCase):
	def setUp(self):
		self.user = self._create_health_user("health-sidecar@example.com")
		self.original_config = {
			"mcp_assertion_secret": frappe.conf.get("mcp_assertion_secret"),
			"mcp_assertion_issuer": frappe.conf.get("mcp_assertion_issuer"),
			"mcp_assertion_audience": frappe.conf.get("mcp_assertion_audience"),
			"mcp_required_scope": frappe.conf.get("mcp_required_scope"),
		}
		frappe.conf.update(
			{
				"mcp_assertion_secret": TEST_SECRET,
				"mcp_assertion_issuer": "test-mcp",
				"mcp_assertion_audience": "test-frappe",
				"mcp_required_scope": "personal:mcp",
			}
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		for key, value in self.original_config.items():
			if value is None:
				frappe.conf.pop(key, None)
			else:
				frappe.conf[key] = value

	def test_assertion_authenticates_user_and_creates_owned_record(self):
		self._set_assertion_header(self._assertion())

		result = sidecar_api.create_health_body_metrics(
			measurement_time="2026-07-31",
			weight=64.2,
			height=180,
		)

		doc = frappe.get_doc("Health Body Metrics", result["name"])
		self.assertEqual(doc.owner, self.user.name)
		self.assertEqual(doc.source, "MCP")
		self.assertEqual(frappe.session.user, "Administrator")

	def test_assertion_cannot_be_replayed(self):
		assertion = self._assertion()
		self._set_assertion_header(assertion)
		sidecar_api.get_health_body_metrics()

		self._set_assertion_header(assertion)
		with self.assertRaises(frappe.AuthenticationError):
			sidecar_api.get_health_body_metrics()

	def test_assertion_requires_valid_signature(self):
		self._set_assertion_header(self._assertion(secret="wrong-secret-that-is-also-long-enough"))

		with self.assertRaises(frappe.AuthenticationError):
			sidecar_api.get_health_body_metrics()

	def _assertion(self, *, secret=TEST_SECRET):
		now = datetime.now(UTC)
		return jwt.encode(
			{
				"sub": self.user.name,
				"iss": "test-mcp",
				"aud": "test-frappe",
				"scope": "openid personal:mcp",
				"iat": now,
				"exp": now + timedelta(seconds=60),
				"jti": str(uuid4()),
			},
			secret,
			algorithm="HS256",
		)

	def _set_assertion_header(self, assertion):
		frappe.local.request = frappe._dict(headers={"X-Personal-MCP-Assertion": assertion})

	def _create_health_user(self, email):
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				doctype="User",
				email=email,
				first_name="Health",
				last_name="Sidecar",
				send_welcome_email=0,
			).insert(ignore_permissions=True)

		if "Health User" not in frappe.get_roles(user.name):
			user.add_roles("Health User")
		return user

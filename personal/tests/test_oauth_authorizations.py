import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from personal.oauth_authorizations import get_authorizations, revoke_authorization


class TestOAuthAuthorizations(IntegrationTestCase):
	def setUp(self):
		test_id = frappe.generate_hash(length=8)
		self.user = self._create_user(f"oauth-owner-{test_id}@example.com")
		self.other_user = self._create_user(f"oauth-other-{test_id}@example.com")
		self.client = self._create_oauth_client()
		self.own_token = self._create_token(self.user.name)
		self.other_token = self._create_token(self.other_user.name)
		frappe.set_user(self.user.name)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_lists_only_current_users_authorizations_without_secrets(self):
		authorizations = get_authorizations()

		self.assertEqual(len(authorizations), 1)
		self.assertEqual(authorizations[0]["app_name"], self.client.app_name)
		self.assertEqual(authorizations[0]["client_id"], self.client.name)
		self.assertNotIn("access_token", authorizations[0])
		self.assertNotIn("refresh_token", authorizations[0])

	def test_revoke_marks_all_current_users_tokens_as_revoked(self):
		self._create_token(self.user.name)

		result = revoke_authorization(self.client.name)

		self.assertEqual(result["revoked"], 2)
		self.assertEqual(
			frappe.get_all(
				"OAuth Bearer Token",
				filters={"client": self.client.name, "status": "Active", "user": self.user.name},
			),
			[],
		)
		self.assertEqual(frappe.db.get_value("OAuth Bearer Token", self.other_token.name, "status"), "Active")

	def test_guest_cannot_list_or_revoke_authorizations(self):
		frappe.set_user("Guest")

		self.assertRaises(frappe.AuthenticationError, get_authorizations)
		self.assertRaises(frappe.AuthenticationError, revoke_authorization, self.client.name)

	def _create_user(self, email: str):
		if frappe.db.exists("User", email):
			return frappe.get_doc("User", email)
		return frappe.get_doc(
			doctype="User",
			email=email,
			first_name="OAuth",
			last_name="User",
			send_welcome_email=0,
		).insert(ignore_permissions=True)

	def _create_oauth_client(self):
		return frappe.get_doc(
			doctype="OAuth Client",
			app_name=f"Personal MCP Test {frappe.generate_hash(length=8)}",
			default_redirect_uri="https://example.com/oauth/callback",
			grant_type="Authorization Code",
			redirect_uris="https://example.com/oauth/callback",
			response_type="Code",
			scopes="openid personal:read",
		).insert(ignore_permissions=True)

	def _create_token(self, user: str):
		return frappe.get_doc(
			doctype="OAuth Bearer Token",
			access_token=frappe.generate_hash(length=32),
			client=self.client.name,
			expiration_time=add_to_date(now_datetime(), hours=1),
			expires_in=3600,
			refresh_token=frappe.generate_hash(length=32),
			scopes="openid personal:read",
			status="Active",
			user=user,
		).insert(ignore_permissions=True)

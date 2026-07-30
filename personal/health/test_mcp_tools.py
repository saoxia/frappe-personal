import frappe
from frappe.tests import IntegrationTestCase

from personal.health.mcp_tools import (
	create_health_body_metrics,
	get_health_body_metrics,
)


class TestHealthBodyMetricsMCP(IntegrationTestCase):
	def setUp(self):
		self.user = self._create_health_user("health-mcp@example.com")
		frappe.set_user(self.user.name)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_creates_metrics_from_confirmed_values(self):
		result = create_health_body_metrics(
			measurement_time="2026-07-30",
			weight=64.2,
			height=180,
			body_fat_percentage=14,
			fat_mass=9,
			basal_metabolic_rate=1562,
			muscle_mass=52.2,
			muscle_percentage=81.3,
			protein_mass=10.7,
			protein_percentage=16.7,
			body_water_mass=40.9,
			body_water_percentage=63.7,
			bone_mineral_mass=3,
			bone_mineral_percentage=4.7,
			skeletal_muscle_mass=29.8,
			client_request_id="body-scale-report-2026-07-30",
		)

		doc = frappe.get_doc("Health Body Metrics", result["name"])
		self.assertTrue(result["created"])
		self.assertEqual(doc.owner, self.user.name)
		self.assertEqual(doc.source, "MCP")
		self.assertEqual(doc.bmi, 19.81)
		self.assertEqual(doc.measurement_time_is_estimated, 1)

	def test_repeated_client_request_is_idempotent(self):
		first = self._create_metrics(client_request_id="same-request")
		second = self._create_metrics(client_request_id="same-request")

		self.assertTrue(first["created"])
		self.assertFalse(second["created"])
		self.assertEqual(first["name"], second["name"])

	def test_list_respects_owner_permissions(self):
		own_record = self._create_metrics()["name"]

		frappe.set_user("Administrator")
		other_user = self._create_health_user("health-mcp-other@example.com")
		frappe.set_user(other_user.name)
		self._create_metrics()

		frappe.set_user(self.user.name)
		result = get_health_body_metrics()

		self.assertEqual([record["name"] for record in result["records"]], [own_record])

	def _create_metrics(self, **overrides):
		values = {
			"measurement_time": "2026-07-30T17:30:00",
			"weight": 64.2,
			"height": 180,
		}
		values.update(overrides)
		return create_health_body_metrics(**values)

	def _create_health_user(self, email):
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				doctype="User",
				email=email,
				first_name="Health",
				last_name="MCP",
				send_welcome_email=0,
			).insert(ignore_permissions=True)

		if "Health User" not in frappe.get_roles(user.name):
			user.add_roles("Health User")
		return user

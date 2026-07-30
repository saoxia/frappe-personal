# Copyright (c) 2026, Personal and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime


class TestHealthBodyMetrics(IntegrationTestCase):
	def test_calculates_bmi(self):
		doc = self._new_document(weight=70, height=175).insert()

		self.assertEqual(doc.bmi, 22.86)

	def test_rejects_non_positive_weight(self):
		doc = self._new_document(weight=0)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_negative_mass(self):
		doc = self._new_document(fat_mass=-1)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_percentage_outside_range(self):
		doc = self._new_document(body_fat_percentage=101)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_owner_permissions_isolate_health_records(self):
		first_user = self._create_health_user("health-owner-a@example.com")
		second_user = self._create_health_user("health-owner-b@example.com")

		try:
			frappe.set_user(first_user.name)
			doc = self._new_document().insert()

			frappe.set_user(second_user.name)
			self.assertFalse(
				frappe.has_permission("Health Body Metrics", "read", doc=doc)
			)
		finally:
			frappe.set_user("Administrator")

	def _new_document(self, **overrides):
		values = {
			"doctype": "Health Body Metrics",
			"measurement_time": now_datetime(),
			"weight": 70,
			"height": 175,
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def _create_health_user(self, email):
		user = frappe.get_doc(
			doctype="User",
			email=email,
			first_name="Health",
			last_name="User",
			send_welcome_email=0,
		).insert(ignore_permissions=True)
		user.add_roles("Health User")
		return user

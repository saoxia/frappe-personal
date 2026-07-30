# Copyright (c) 2026, Personal and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestHealthFoodItem(IntegrationTestCase):
	def test_calculates_calories(self):
		doc = self._new_document(
			food_name="Calorie Test Food",
			protein=10,
			fat=5,
			carbohydrate=20,
		).insert()

		self.assertEqual(doc.calories, 165)

	def test_rejects_negative_nutrients(self):
		doc = self._new_document(food_name="Negative Nutrient Test", protein=-1)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_requires_base_unit(self):
		doc = self._new_document(food_name="Missing Unit Test", base_unit="")

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def _new_document(self, **overrides):
		values = {
			"doctype": "Health Food Item",
			"food_name": "Test Food",
			"category": "Staples",
			"base_unit": "100 g",
			"protein": 0,
			"fat": 0,
			"carbohydrate": 0,
		}
		values.update(overrides)
		return frappe.get_doc(values)

# Copyright (c) 2026, Personal and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HealthFoodItem(Document):
	NUTRIENT_FIELDS = ("protein", "fat", "carbohydrate")

	def validate(self):
		self._validate_nutrients()
		self.calories = self._calculate_calories()

	def _validate_nutrients(self):
		for fieldname in self.NUTRIENT_FIELDS:
			if flt(self.get(fieldname)) < 0:
				frappe.throw(
					_("{0} cannot be negative.").format(self._field_label(fieldname))
				)

	def _calculate_calories(self):
		protein_calories = flt(self.protein) * 4
		fat_calories = flt(self.fat) * 9
		carbohydrate_calories = flt(self.carbohydrate) * 4
		return flt(protein_calories + fat_calories + carbohydrate_calories, 2)

	def _field_label(self, fieldname):
		return _(self.meta.get_field(fieldname).label)

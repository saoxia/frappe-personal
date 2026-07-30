# Copyright (c) 2026, Personal and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HealthBodyMetrics(Document):
	PERCENTAGE_FIELDS = (
		"body_fat_percentage",
		"muscle_percentage",
		"protein_percentage",
		"body_water_percentage",
		"bone_mineral_percentage",
	)
	NON_NEGATIVE_FIELDS = (
		"fat_mass",
		"basal_metabolic_rate",
		"muscle_mass",
		"protein_mass",
		"body_water_mass",
		"bone_mineral_mass",
		"skeletal_muscle_mass",
	)

	def validate(self):
		self._validate_positive("weight")
		self._validate_positive("height")
		self._validate_non_negative_values()
		self._validate_percentages()
		self.bmi = self._calculate_bmi()

	def _validate_positive(self, fieldname):
		if flt(self.get(fieldname)) <= 0:
			frappe.throw(
				_("{0} must be greater than zero.").format(self._field_label(fieldname))
			)

	def _validate_non_negative_values(self):
		for fieldname in self.NON_NEGATIVE_FIELDS:
			if flt(self.get(fieldname)) < 0:
				frappe.throw(
					_("{0} cannot be negative.").format(self._field_label(fieldname))
				)

	def _validate_percentages(self):
		for fieldname in self.PERCENTAGE_FIELDS:
			value = flt(self.get(fieldname))
			if value < 0 or value > 100:
				frappe.throw(
					_("{0} must be between 0 and 100.").format(
						self._field_label(fieldname)
					)
				)

	def _calculate_bmi(self):
		height_in_meters = flt(self.height) / 100
		return flt(flt(self.weight) / (height_in_meters**2), 2)

	def _field_label(self, fieldname):
		return _(self.meta.get_field(fieldname).label)

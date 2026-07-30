from __future__ import annotations

import re
from hashlib import sha256

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_datetime

BODY_METRICS_FIELDS = (
	"measurement_time",
	"measurement_time_is_estimated",
	"weight",
	"height",
	"bmi",
	"body_fat_percentage",
	"fat_mass",
	"basal_metabolic_rate",
	"muscle_mass",
	"muscle_percentage",
	"protein_mass",
	"protein_percentage",
	"body_water_mass",
	"body_water_percentage",
	"bone_mineral_mass",
	"bone_mineral_percentage",
	"skeletal_muscle_mass",
	"source",
)
DATE_ONLY_PATTERN = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$")


def create_health_body_metrics(
	measurement_time: str,
	weight: float,
	height: float,
	body_fat_percentage: float | None = None,
	fat_mass: float | None = None,
	basal_metabolic_rate: int | None = None,
	muscle_mass: float | None = None,
	muscle_percentage: float | None = None,
	protein_mass: float | None = None,
	protein_percentage: float | None = None,
	body_water_mass: float | None = None,
	body_water_percentage: float | None = None,
	bone_mineral_mass: float | None = None,
	bone_mineral_percentage: float | None = None,
	skeletal_muscle_mass: float | None = None,
	client_request_id: str | None = None,
	measurement_time_is_estimated: bool = False,
) -> dict:
	_require_authenticated_user()
	client_request_id = _clean_request_id(client_request_id)

	if existing := _find_existing_request(client_request_id):
		return _creation_result(existing, created=False)

	date_only = bool(DATE_ONLY_PATTERN.fullmatch(measurement_time.strip()))
	values = {
		"doctype": "Health Body Metrics",
		"measurement_time": get_datetime(measurement_time),
		"measurement_time_is_estimated": date_only or measurement_time_is_estimated,
		"weight": weight,
		"height": height,
		"source": "MCP",
		"client_request_id": client_request_id,
		"client_request_key": _request_key(client_request_id),
	}
	values.update(
		{
			"body_fat_percentage": body_fat_percentage,
			"fat_mass": fat_mass,
			"basal_metabolic_rate": basal_metabolic_rate,
			"muscle_mass": muscle_mass,
			"muscle_percentage": muscle_percentage,
			"protein_mass": protein_mass,
			"protein_percentage": protein_percentage,
			"body_water_mass": body_water_mass,
			"body_water_percentage": body_water_percentage,
			"bone_mineral_mass": bone_mineral_mass,
			"bone_mineral_percentage": bone_mineral_percentage,
			"skeletal_muscle_mass": skeletal_muscle_mass,
		}
	)

	doc = frappe.get_doc(values).insert()
	return _creation_result(doc, created=True)


def get_health_body_metrics(
	name: str | None = None,
	start_date: str | None = None,
	end_date: str | None = None,
	limit: int = 20,
) -> dict:
	_require_authenticated_user()

	if name:
		doc = frappe.get_doc("Health Body Metrics", name)
		doc.check_permission("read")
		return {"records": [_serialize(doc)]}

	records = frappe.get_list(
		"Health Body Metrics",
		filters=_date_filters(start_date, end_date),
		fields=["name", *BODY_METRICS_FIELDS],
		order_by="measurement_time desc",
		limit=max(1, min(cint(limit), 100)),
	)
	return {"records": [_serialize(record) for record in records]}


def _require_authenticated_user():
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication is required."), frappe.PermissionError)


def _clean_request_id(client_request_id):
	if not client_request_id:
		return None

	client_request_id = client_request_id.strip()
	if len(client_request_id) > 140:
		frappe.throw(_("Client Request ID cannot exceed 140 characters."))
	return client_request_id


def _find_existing_request(client_request_id):
	if not client_request_id:
		return None

	name = frappe.db.get_value(
		"Health Body Metrics",
		{"client_request_key": _request_key(client_request_id)},
	)
	return frappe.get_doc("Health Body Metrics", name) if name else None


def _request_key(client_request_id):
	if not client_request_id:
		return None

	value = f"{frappe.session.user}\0{client_request_id}"
	return sha256(value.encode()).hexdigest()


def _creation_result(doc, *, created):
	warnings = []
	if doc.measurement_time_is_estimated:
		warnings.append(_("The source did not provide an exact measurement time."))
	if not created:
		warnings.append(_("This client request was already processed."))

	return {
		"success": True,
		"created": created,
		"name": doc.name,
		"record": _serialize(doc),
		"warnings": warnings,
	}


def _serialize(doc):
	record = {
		"name": doc.name,
		**{fieldname: doc.get(fieldname) for fieldname in BODY_METRICS_FIELDS},
	}
	if record["measurement_time"]:
		record["measurement_time"] = str(record["measurement_time"])
	return record


def _date_filters(start_date, end_date):
	filters = []
	if start_date:
		filters.append(["measurement_time", ">=", get_datetime(start_date)])
	if end_date:
		filters.append(["measurement_time", "<", get_datetime(add_days(end_date, 1))])
	return filters

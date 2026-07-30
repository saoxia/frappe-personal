from __future__ import annotations

import re
from hashlib import sha256

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_datetime

from personal.health.mcp_schemas import (
	CREATE_BODY_METRICS_SCHEMA,
	GET_BODY_METRICS_SCHEMA,
)
from personal.mcp import mcp

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


@mcp.tool(
	input_schema=CREATE_BODY_METRICS_SCHEMA,
	annotations={
		"title": "Create body metrics",
		"readOnlyHint": False,
		"destructiveHint": False,
		"idempotentHint": False,
		"openWorldHint": False,
	}
)
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
	"""Create a body-composition measurement after the user confirms parsed values.

	Args:
		measurement_time: Measurement date or local date-time. Use YYYY-MM-DD when
			the source has no exact time.
		weight: Body weight in kilograms.
		height: Height in centimeters.
		body_fat_percentage: Body fat percentage.
		fat_mass: Fat mass in kilograms.
		basal_metabolic_rate: Basal metabolic rate in kilocalories per day.
		muscle_mass: Muscle mass in kilograms.
		muscle_percentage: Muscle percentage.
		protein_mass: Protein mass in kilograms.
		protein_percentage: Protein percentage.
		body_water_mass: Body water mass in kilograms.
		body_water_percentage: Body water percentage.
		bone_mineral_mass: Bone mineral mass in kilograms.
		bone_mineral_percentage: Bone mineral percentage.
		skeletal_muscle_mass: Skeletal muscle mass in kilograms.
		client_request_id: Optional unique ID used to make retries idempotent.
		measurement_time_is_estimated: Set when the supplied time is approximate.
	"""
	_require_authenticated_user()
	client_request_id = _clean_request_id(client_request_id)

	if existing := _find_existing_request(client_request_id):
		return _creation_result(existing, created=False)

	date_only = bool(DATE_ONLY_PATTERN.fullmatch(measurement_time.strip()))
	values = {
		"doctype": "Health Body Metrics",
		"measurement_time": get_datetime(measurement_time),
		"measurement_time_is_estimated": date_only
		or measurement_time_is_estimated,
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


@mcp.tool(
	input_schema=GET_BODY_METRICS_SCHEMA,
	annotations={
		"title": "Get body metrics",
		"readOnlyHint": True,
		"destructiveHint": False,
		"idempotentHint": True,
		"openWorldHint": False,
	}
)
def get_health_body_metrics(
	name: str | None = None,
	start_date: str | None = None,
	end_date: str | None = None,
	limit: int = 20,
) -> dict:
	"""Get one body measurement or list the current user's recent measurements.

	Args:
		name: Optional Health Body Metrics record name.
		start_date: Optional inclusive measurement start date.
		end_date: Optional inclusive measurement end date.
		limit: Maximum records to return, between 1 and 100.
	"""
	_require_authenticated_user()

	if name:
		doc = frappe.get_doc("Health Body Metrics", name)
		doc.check_permission("read")
		return {"records": [_serialize(doc)]}

	filters = _date_filters(start_date, end_date)
	records = frappe.get_list(
		"Health Body Metrics",
		filters=filters,
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
		{
			"client_request_key": _request_key(client_request_id),
		},
	)
	if not name:
		return None
	return frappe.get_doc("Health Body Metrics", name)


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
		filters.append(
			["measurement_time", "<", get_datetime(add_days(end_date, 1))]
		)
	return filters

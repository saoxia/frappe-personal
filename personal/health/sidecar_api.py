from __future__ import annotations

import frappe

from personal.health.body_metrics_service import (
	create_health_body_metrics as create_metrics,
)
from personal.health.body_metrics_service import (
	get_health_body_metrics as get_metrics,
)
from personal.sidecar_auth import authenticated_sidecar_user


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_health_body_metrics(**values) -> dict:
	with authenticated_sidecar_user():
		return create_metrics(**values)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def get_health_body_metrics(**filters) -> dict:
	with authenticated_sidecar_user():
		return get_metrics(**filters)

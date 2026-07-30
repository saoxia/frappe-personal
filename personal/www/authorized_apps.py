import frappe
from frappe import _
from frappe.utils import format_datetime

from personal.oauth_authorizations import get_authorizations


def get_context(context):
	context.no_cache = 1
	context.title = _("Authorized Apps")
	context.is_guest = frappe.session.user == "Guest"
	context.authorizations = [] if context.is_guest else _get_display_authorizations()


def _get_display_authorizations() -> list[dict]:
	authorizations = get_authorizations()
	for authorization in authorizations:
		authorization["authorized_on_display"] = format_datetime(authorization["authorized_on"])
		authorization["expires_at_display"] = format_datetime(authorization["expires_at"])
	return authorizations

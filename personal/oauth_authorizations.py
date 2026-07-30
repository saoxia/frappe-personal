from collections import defaultdict

import frappe
from frappe import _


@frappe.whitelist(methods=["GET"])
def get_authorizations() -> list[dict]:
	"""Return OAuth applications authorized by the current user."""
	user = _require_authenticated_user()
	tokens = frappe.get_all(
		"OAuth Bearer Token",
		filters={"user": user, "status": "Active"},
		fields=["client", "scopes", "creation", "expiration_time"],
		order_by="creation desc",
	)
	if not tokens:
		return []

	app_names = _get_app_names({token.client for token in tokens})
	return _group_authorizations(tokens, app_names)


@frappe.whitelist(methods=["POST"])
def revoke_authorization(client_id: str) -> dict:
	"""Revoke every active token issued to one client for the current user."""
	user = _require_authenticated_user()
	token_names = frappe.get_all(
		"OAuth Bearer Token",
		filters={
			"client": client_id,
			"status": "Active",
			"user": user,
		},
		pluck="name",
	)

	for token_name in token_names:
		frappe.db.set_value(
			"OAuth Bearer Token",
			token_name,
			"status",
			"Revoked",
			update_modified=True,
		)

	return {"client_id": client_id, "revoked": len(token_names)}


def _require_authenticated_user() -> str:
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in to manage authorized applications."), frappe.AuthenticationError)
	return user


def _get_app_names(client_ids: set[str]) -> dict[str, str]:
	clients = frappe.get_all(
		"OAuth Client",
		filters={"name": ["in", list(client_ids)]},
		fields=["name", "app_name"],
	)
	return {client.name: client.app_name for client in clients}


def _group_authorizations(tokens: list, app_names: dict[str, str]) -> list[dict]:
	grouped = defaultdict(list)
	for token in tokens:
		grouped[token.client].append(token)

	authorizations = []
	for client_id, client_tokens in grouped.items():
		authorizations.append(
			{
				"app_name": app_names.get(client_id, _("Unknown application")),
				"authorized_on": min(token.creation for token in client_tokens),
				"client_id": client_id,
				"expires_at": max(token.expiration_time for token in client_tokens),
				"scopes": _collect_scopes(client_tokens),
				"session_count": len(client_tokens),
			}
		)

	return sorted(authorizations, key=lambda item: item["authorized_on"], reverse=True)


def _collect_scopes(tokens: list) -> list[str]:
	scopes = set()
	for token in tokens:
		scopes.update((token.scopes or "").split())
	return sorted(scopes)

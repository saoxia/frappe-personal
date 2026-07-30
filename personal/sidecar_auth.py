from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import frappe
import jwt
from frappe import _

ASSERTION_HEADER = "X-Personal-MCP-Assertion"
DEFAULT_ISSUER = "personal-mcp-sidecar"
DEFAULT_AUDIENCE = "personal-frappe-api"
DEFAULT_SCOPE = "personal:mcp"


@contextmanager
def authenticated_sidecar_user():
	claims = _verify_assertion(_get_assertion())
	original_user = frappe.session.user
	frappe.set_user(claims["sub"])
	try:
		yield claims
	finally:
		frappe.set_user(original_user)


def _get_assertion() -> str:
	assertion = frappe.get_request_header(ASSERTION_HEADER)
	if not assertion:
		frappe.throw(_("Missing MCP sidecar assertion."), frappe.AuthenticationError)
	return assertion


def _verify_assertion(assertion: str) -> dict:
	secret = frappe.conf.get("mcp_assertion_secret")
	if not secret or len(secret) < 32:
		frappe.throw(_("MCP sidecar authentication is not configured."), frappe.AuthenticationError)

	try:
		claims = jwt.decode(
			assertion,
			secret,
			algorithms=["HS256"],
			audience=frappe.conf.get("mcp_assertion_audience") or DEFAULT_AUDIENCE,
			issuer=frappe.conf.get("mcp_assertion_issuer") or DEFAULT_ISSUER,
			options={
				"require": ["sub", "aud", "iss", "exp", "iat", "jti", "scope"],
			},
		)
	except jwt.PyJWTError:
		frappe.throw(_("Invalid or expired MCP sidecar assertion."), frappe.AuthenticationError)

	required_scope = frappe.conf.get("mcp_required_scope") or DEFAULT_SCOPE
	if required_scope not in claims["scope"].split():
		frappe.throw(_("The MCP sidecar assertion has insufficient scope."), frappe.PermissionError)

	user = frappe.db.get_value("User", claims["sub"], ["name", "enabled"], as_dict=True)
	if not user or not user.enabled:
		frappe.throw(_("The MCP user is unavailable."), frappe.AuthenticationError)

	_prevent_replay(claims)
	return claims


def _prevent_replay(claims: dict):
	expires_in = max(1, int(claims["exp"] - datetime.now(UTC).timestamp()))
	cache_key = frappe.cache.make_key(f"mcp-sidecar-assertion:{claims['jti']}")
	if not frappe.cache.set(name=cache_key, value="1", ex=expires_in, nx=True):
		frappe.throw(_("The MCP sidecar assertion was already used."), frappe.AuthenticationError)

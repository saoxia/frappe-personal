import frappe_mcp

mcp = frappe_mcp.MCP("personal-health")


@mcp.register()
def handle_mcp():
	from personal.health import mcp_tools  # noqa: F401

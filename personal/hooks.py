app_name = "personal"
app_title = "Personal"
app_publisher = "Personal"
app_description = "Personal information management system"
app_email = "lingyu_li@foxmail.com"
app_license = "mit"

required_apps = ["flow"]

user_data_fields = [
	{"doctype": "Health Body Metrics", "filter_by": "owner"},
	{"doctype": "Health Food Item", "filter_by": "owner"},
]
website_route_rules = [
	{"from_route": "/authorized-apps", "to_route": "authorized_apps"},
]

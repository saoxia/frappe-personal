OPTIONAL_NUMBER = {"type": ["number", "null"]}

CREATE_BODY_METRICS_SCHEMA = {
	"type": "object",
	"additionalProperties": False,
	"properties": {
		"measurement_time": {
			"type": "string",
			"description": "Measurement date or local date-time.",
		},
		"weight": {
			"type": "number",
			"description": "Body weight in kilograms.",
		},
		"height": {
			"type": "number",
			"description": "Height in centimeters.",
		},
		"body_fat_percentage": OPTIONAL_NUMBER,
		"fat_mass": OPTIONAL_NUMBER,
		"basal_metabolic_rate": {"type": ["integer", "null"]},
		"muscle_mass": OPTIONAL_NUMBER,
		"muscle_percentage": OPTIONAL_NUMBER,
		"protein_mass": OPTIONAL_NUMBER,
		"protein_percentage": OPTIONAL_NUMBER,
		"body_water_mass": OPTIONAL_NUMBER,
		"body_water_percentage": OPTIONAL_NUMBER,
		"bone_mineral_mass": OPTIONAL_NUMBER,
		"bone_mineral_percentage": OPTIONAL_NUMBER,
		"skeletal_muscle_mass": OPTIONAL_NUMBER,
		"client_request_id": {
			"type": ["string", "null"],
			"description": "Unique client ID for idempotent retries.",
			"maxLength": 140,
		},
		"measurement_time_is_estimated": {
			"type": "boolean",
			"default": False,
		},
	},
	"required": ["measurement_time", "weight", "height"],
}

GET_BODY_METRICS_SCHEMA = {
	"type": "object",
	"additionalProperties": False,
	"properties": {
		"name": {"type": ["string", "null"]},
		"start_date": {"type": ["string", "null"]},
		"end_date": {"type": ["string", "null"]},
		"limit": {
			"type": "integer",
			"minimum": 1,
			"maximum": 100,
			"default": 20,
		},
	},
}

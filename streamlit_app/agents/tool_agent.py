"""Tool Agent: internal Python functions exposed to the Response Agent's
OpenAI function-calling loop. Reuses backend.agent.tools.lookup_disease
(same knowledge base, same proven exact/fuzzy-match logic) rather than
reimplementing it, and adds a dashboard-stats lookup."""

from backend.agent.tools import lookup_disease
from ..core import db

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_disease",
            "description": (
                "Look up symptoms and precautionary/treatment measures for a crop "
                "disease class detected by the vision model. Always call this before "
                "giving disease-specific advice so answers are grounded in the "
                "knowledge base rather than guessed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": (
                            "Exact class name, e.g. 'Tomato___Late_blight', or a "
                            "human-readable disease/crop name if the exact class is unknown."
                        ),
                    }
                },
                "required": ["class_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_stats",
            "description": (
                "Return live usage statistics for this CropDoc deployment: total "
                "predictions made, most commonly detected diseases, chat activity."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_FUNCTIONS = {
    "lookup_disease": lookup_disease,
    "get_dashboard_stats": lambda: db.get_dashboard_stats(),
}

from langflow import CustomComponent
from langflow.field_typing import Text

class SimpleTextDisplay(CustomComponent):
    display_name = "Text Display"
    description = "Simple text display for Langflow playground"
    icon = "type"

    def build_config(self):
        return {}

    def build_inputs(self):
        return {
            "text": {
                "display_name": "Text",
                "type": "str",
                "multiline": True,
                "info": "Text content to display"
            }
        }

    def build(self, text: str, **kwargs) -> str:
        """Simple text pass-through for display"""
        return str(text) if text else "No content provided"
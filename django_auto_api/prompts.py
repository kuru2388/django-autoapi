# django_auto_api/prompts.py
from typing import List, Dict


def build_serializer_prompt(
    app_label: str,
    model_name: str,
    fields: List[Dict[str, str]],
) -> str:
    """
    Build a user prompt that describes the model and asks for a DRF ModelSerializer.
    fields: [{ "name": "title", "type": "CharField" }, ...]
    """
    fields_lines = "\n".join(
        f"- {f['name']}: {f['type']}" for f in fields
    )

    return f"""
You are given a Django model definition.

App label: {app_label}
Model name: {model_name}

Fields:
{fields_lines}

Task:
Write a Django REST Framework ModelSerializer named {model_name}Serializer for this model.

Rules:
- Import from rest_framework import serializers.
- Use serializers.ModelSerializer.
- Define Meta.model = {model_name}.
- Set Meta.fields = "__all__".
- Do NOT include any explanation or comments.
- Output ONLY valid Python code that can be appended to a serializers module.
"""

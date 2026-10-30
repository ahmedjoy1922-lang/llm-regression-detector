from pathlib import Path

import yaml
from jinja2 import Template
from pydantic import BaseModel, ConfigDict


# Validate the versioned prompt file before rendering it.
class PromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    system: str
    user_template: str


# Parse one YAML prompt into the typed prompt contract.
def load_prompt(path: Path) -> PromptSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PromptSpec.model_validate(data)


# Render only the fictional ticket into the user template.
def render_ticket(spec: PromptSpec, ticket_text: str) -> str:
    return Template(spec.user_template).render(ticket_text=ticket_text)
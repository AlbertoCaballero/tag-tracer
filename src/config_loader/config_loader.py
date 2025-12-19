"""Configuration models and loaders for TagTracer.
Defines Pydantic schemas for domain rules, validators, and workflow settings.

TODO:
- Implement Pydantic models
- Add YAML configuration loader
- Integrate with Excel loader
"""

class ConfigLoader:
    def __init__(self, domains=None, rules=None):
        self.domains = domains or []
        self.rules = rules or []


@classmethod
def from_yaml(cls, path: str):
    # TODO: Implement YAML loading
    pass

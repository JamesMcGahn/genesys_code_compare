from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityCode:
    ac_id: str
    name: str
    default_code: bool
    category: str
    default_name_changed: bool

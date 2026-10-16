from dataclasses import dataclass


@dataclass()
class Region:
    name: str
    login_url: str
    api_url: str

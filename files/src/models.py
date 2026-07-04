from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator


class Config(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda name: f'wc_{name}',
    )
    compose_name: str
    compose_service_base: dict[str, Any]
    compose_logging_driver: str
    compose_logging_options: dict[str, Any]
    compose_default_attestations: bool
    traefik_admin_host: str
    traefik_admin_use_internal: bool
    traefik_admin_use_auth: bool


class XWebConductorRoot(BaseModel):
    group: Optional[str] = 'User Services'


class Repo(BaseModel):
    url: str
    mtime: Optional[bool] = False


class Route(BaseModel):
    port: Optional[int] = None
    host: Optional[str] = None
    path: Optional[str] = None
    admin: bool = False
    internal: Optional[bool] = None
    auth: Optional[bool] = None
    location: Optional[str] = None
    priority: Optional[int] = None


class XWebConductorService(BaseModel):
    _service_name: str = PrivateAttr('')
    name: Optional[str] = None
    description: Optional[str] = None
    repo: Optional[Repo] = None
    route: Optional[Route] = None
    routes: Optional[dict[str, Route]] = None
    homepage: Optional[dict[str, Any]] | bool = False

    @property
    def service_name(self) -> str:
        return self._service_name


class ComposeService(BaseModel):
    _name: str = PrivateAttr('')
    x_web_conductor: Optional[XWebConductorService] = Field(None, alias='x-web-conductor')

    @property
    def name(self) -> str:
        return self._name


class ComposeFile(BaseModel):
    x_web_conductor: XWebConductorRoot = Field(default_factory=XWebConductorRoot, alias='x-web-conductor')
    services: dict[str, ComposeService] = Field(default_factory=dict)

    @model_validator(mode='after')
    def set_service_names(self) -> 'ComposeFile':
        for name, service in self.services.items():
            service._name = name
            if service.x_web_conductor:
                service.x_web_conductor._service_name = name
        return self

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:

    user_id: str
    tenant_id: str
    permissions: frozenset[str]
    group_ids: frozenset[str] = field(default_factory=frozenset)
    max_classification_level: int = 1


@dataclass(frozen=True)
class SecurityContext:

    principal: Principal
    request_id: str

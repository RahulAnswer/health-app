from dataclasses import dataclass
from typing import Protocol, List, Dict, Any, Optional

@dataclass
class PatientData:
    name: Optional[str]
    sex: Optional[str]  # "M"/"F"
    age: Optional[float]
    labs: Dict[str, float]
    flags: Dict[str, Any]

@dataclass
class ResultItem:
    metric: str
    value: Optional[float] | str
    interpretation: str
    severity: str  # "low" | "indeterminate" | "high" | "info"

class HealthModule(Protocol):
    id: str
    title: str
    def inputs(self, data: PatientData) -> PatientData: ...
    def compute(self, data: PatientData) -> List[ResultItem]: ...
    def render(self, results: List[ResultItem]) -> None: ...
    def to_pdf(self, results: List[ResultItem]) -> List[list[str]]: ...
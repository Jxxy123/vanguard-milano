from pydantic import BaseModel, Field
from typing import List, Optional


class AgentStep(BaseModel):
    """Represents a single step in the agent's autonomous reasoning loop."""
    step:   str
    detail: str
    status: str   # "ok" | "running" | "warning" | "error"
    ts:     str   # UTC time string HH:MM:SS


class LogisticsHub(BaseModel):
    name:             str
    location:         str
    capacity_status:  str


class X402Settlement(BaseModel):
    transaction_id: str
    amount:         float
    currency:       str
    recipient:      str
    status:         str
    reason:         str
    block_ref:      Optional[str] = None


class RerouteManifest(BaseModel):
    strike_detected:    bool
    strike_level:       str = Field(..., description="None | Low | Medium | High | Critical | Error")
    affected_routes:    List[str]
    alternative_hubs:   List[LogisticsHub]
    rerouting_plan:     str
    payment_settlement: Optional[X402Settlement] = None
    timestamp:          str


class StatusResponse(BaseModel):
    strike_level:   str
    active_reroutes: bool
    manifest:       Optional[RerouteManifest] = None
    agent_steps:    List[AgentStep] = []
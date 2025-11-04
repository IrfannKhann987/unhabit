from pydantic import BaseModel
from typing import Optional, List, Literal,Dict

class Triggers(BaseModel):
    time: List[str] = []
    location: List[str] = []
    emotion: List[str] = []


class Diagnostic(BaseModel):
    habit_category: str
    primary_problem: str
    risk_level: Literal["low", "medium", "high"]
    triggers: Triggers
    why_it_happens: List[str]


class Plan(BaseModel):
    quick_win: str
    tomorrow_task: str
    identity_reframe: str


class SafetyResult(BaseModel):
    risk: Literal["none","self_harm","eating_disorder","severe_addiction","violence","other"]
    action: Literal["allow","block_and_escalate"]
    message: str
class Plan21D(BaseModel):
    phase_summary: str
    daily_tasks: Dict[str, str]
    identity_reframes: List[str]
    environment_changes: List[str]
    replacement_habits: List[str]
    slip_recovery_protocol: str

class PatternAnalysis(BaseModel):
    peak_time: Optional[str] = "unknown"
    location_trigger: Optional[str] = "unknown"
    emotional_trigger: Optional[str] = "unknown"
    confidence: Optional[str] = "low"


class FrictionItem(BaseModel):
    description: str
    emotional_trigger: Optional[str] = None

class FrictionPlan(BaseModel):
    friction_habits: List[FrictionItem]


class ReplacementDopamine(BaseModel):
    alternatives: List[str]

class SlipRecovery(BaseModel):
    strategy: str


class HabitState(BaseModel):
    user_input: str
    safety: Optional[SafetyResult] = None
    diagnostic: Optional[Diagnostic] = None
    plan: Optional[Plan] = None
    coach_reply: Optional[str] = None
    plan21: Optional[Plan21D] = None
    pattern: Optional[PatternAnalysis] = None
    friction: Optional[FrictionPlan] = None
    replacement: Optional[ReplacementDopamine] = None
    slip_recovery: Optional[SlipRecovery] = None
    intent: Optional[str] = None
    next: Optional[str] = None
    habit_category: Optional[str] = None
    peak_time: Optional[str] = None
    location: Optional[str] = None
    emotion: Optional[str] = None
    frequency: Optional[int] = None
    secondary_emotion: List[str] = []




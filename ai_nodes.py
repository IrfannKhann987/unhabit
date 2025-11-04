# ai_nodes.py
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from prompts import DIAGNOSTIC_PROMPT, PLAN_PROMPT, COACH_PROMPT, SAFETY_PROMPT,PLAN_21D_PROMPT,SLIP_RECOVERY_PROMPT,PATTERN_PROMPT,FRICTION_PROMPT,REPLACEMENT_PROMPT,INTENT_PROMPT
from schemas import HabitState, Diagnostic, Plan, SafetyResult, PatternAnalysis, FrictionPlan, ReplacementDopamine, SlipRecovery, Plan21D


load_dotenv()

MODEL_JSON = os.getenv("OPENAI_MODEL_JSON", "gpt-4o-mini")
MODEL_TEXT = os.getenv("OPENAI_MODEL_TEXT", "gpt-4o-mini")

def _llm_json(
    prompt: str,
    max_tokens: int = 800,
    temperature: float = 0.5,
    retries: int = 2
) -> Dict[str, Any]:

    for attempt in range(retries):
        llm = ChatOpenAI(
            model=MODEL_JSON,
            temperature=temperature + (attempt * 0.2),
            response_format={"type": "json_object"},
        )

        resp = llm.invoke(prompt).content
        
        try:
            return json.loads(resp)
        except:
            # strengthen instructions & increase randomness
            prompt += (
                "\nReturn STRICT JSON. No commentary. "
                "Do NOT repeat previous suggestions."
            )
            continue

    return {}



def _llm_text(
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    retries: int = 2,
) -> str:

    for attempt in range(retries):
        llm = ChatOpenAI(
            model=MODEL_TEXT,
            temperature=temperature + (attempt * 0.3)
        )

        try:
            resp = llm.invoke(prompt).content.strip()
            # Filter out trivial / repeated responses
            if len(resp) > 10:
                return resp
        except:
            continue

        # strengthen constraints & vary content
        prompt += "\nRespond differently than the previous attempt."
    
    # last fallback
    return "Try one small action right now that moves you toward your identity goal."


# ---------------- Nodes ---------------- #

def safety_node(state: HabitState) -> Dict[str, Any]:
    data = _llm_json(SAFETY_PROMPT + f"\nUser: {state.user_input}")
    try:
        res = SafetyResult(**data)
    except ValidationError:
        # fallback: allow if schema breaks
        res = SafetyResult(risk="none", action="allow", message="")
    return {"safety": res}

def diagnostic_node(state: HabitState):
    if state.safety and state.safety.action == "block_and_escalate":
        return {}

    enriched_context = f"""
User provided structured metadata:
- Habit Category: {state.habit_category}
- Location: {state.location}
- Peak Time: {state.peak_time}
- Emotion: {state.emotion}
- Secondary Emotions: {state.secondary_emotion}
- Frequency/Week: {state.frequency}
"""

    text = DIAGNOSTIC_PROMPT + enriched_context + "\nUser Description: " + state.user_input
    data = _llm_json(text)
    return {"diagnostic": Diagnostic(**data)}

def plan_node(state: HabitState) -> Dict[str, Any]:
    if not state.diagnostic:
        return {}
    data = _llm_json(PLAN_PROMPT + f"\nDiagnostic JSON:\n{state.diagnostic.model_dump_json()}")
    try:
        plan = Plan(**data)
    except ValidationError:
        # Minimal fallback plan
        plan = Plan(
            quick_win="Put your phone in another room for 30 minutes.",
            tomorrow_task="Disable notifications after 10pm.",
            identity_reframe="I am someone who protects my time."
        )
    return {"plan": plan}

def coach_node(state: HabitState) -> Dict[str, Any]:
    # If blocked by safety, provide the escalation message as the coach reply
    if state.safety and state.safety.action == "block_and_escalate":
        return {"coach_reply": state.safety.message}

    # Otherwise, coach based on plan + user input
    plan_json = state.plan.model_dump() if state.plan else {}
    user = f"User said: {state.user_input}\nPlan: {json.dumps(plan_json)}"
    reply = _llm_text(COACH_PROMPT + "\n" + user)
    return {"coach_reply": reply}


def plan21_node(state: HabitState):
    enriched = f"""
Habit Category: {state.habit_category}
Frequency/Week: {state.frequency}
Peak Time: {state.peak_time}
Location: {state.location}
Emotions: {state.emotion}, {state.secondary_emotion}
"""

    text = PLAN_21D_PROMPT + enriched + "\nUser Description: " + state.user_input
    data = _llm_json(text)
    return {"plan21": Plan21D(**data)}




def pattern_analysis_node(state: HabitState):
    enriched = f"""
User Metadata:
- Peak Time: {state.peak_time}
- Location: {state.location}
- Emotion: {state.emotion}
"""

    text = PATTERN_PROMPT + enriched + "\nUser Description: " + state.user_input
    data = _llm_json(text)

    return {"pattern": PatternAnalysis(**data)}


def friction_upgrade_node(state: HabitState):
    enriched = f"""
Habit Category: {state.habit_category}
Location: {state.location}
Peak Time: {state.peak_time}
Primary Emotion: {state.emotion}
Secondary Emotions: {state.secondary_emotion}
Frequency: {state.frequency}
"""

    data = _llm_json(FRICTION_PROMPT + enriched)

    # Force correct typing if model fails
    if isinstance(data.get("friction_habits"), list):
        cleaned = []
        for item in data["friction_habits"]:
            if isinstance(item, dict) and "description" in item:
                cleaned.append(item)
            else:
                cleaned.append({"description": str(item), "emotional_trigger": None})
        data["friction_habits"] = cleaned

    return {"friction": FrictionPlan(**data)}



import json, random

def replacement_dopamine_node(state: HabitState):
    enriched = f"""
Context:
Habit Category: {state.habit_category}
Primary Emotion: {state.emotion}
Location: {state.location}
Peak Time: {state.peak_time}
Secondary Emotion: {state.secondary_emotion}
Frequency: {state.frequency}
"""

    data = _llm_json(REPLACEMENT_PROMPT + enriched)

    # --- sanitize output (model sometimes returns dict objects) ---
    alts = data.get("alternatives", [])
    cleaned = []

    for a in alts:
        if isinstance(a, dict):
            # if model uses {"action": "..."}
            cleaned.append(a.get("action","").strip())
        else:
            cleaned.append(str(a).strip())

    # ensure we always have at least one option
    if not cleaned:
        cleaned = ["Stand up, stretch arms overhead, 10s."]

    return {"replacement": ReplacementDopamine(alternatives=cleaned)}


    

def slip_recovery_node(state: HabitState):
    enriched = f"""
User slips often during:
- Emotion: {state.emotion}
- Location: {state.location}
Frequency: {state.frequency}
"""

    text = SLIP_RECOVERY_PROMPT + enriched + "\nDescription: " + state.user_input
    data = _llm_json(text)
    return {"slip_recovery": SlipRecovery(**data)}


def fallback_plan21():
    return {
        "phase_summary": "Simple progressive habit reduction.",
        "daily_tasks": {
            f"day_{i+1}": "2-minute urge surfing + phone outside bedroom."
            for i in range(21)
        },
        "identity_reframes": [
            "I choose my attention.",
            "My urges do not define me."
        ],
        "environment_changes": [
            "Charge phone outside bedroom",
            "Disable adult content",
            "Turn off bedtime notifications"
        ],
        "replacement_habits": [
            "Cold water on face",
            "5 pushups",
            "2-minute stretching"
        ],
        "slip_recovery_protocol": "Reflect 60s, increase friction, continue next day."
    }

def intent_node(state: HabitState):
    data = _llm_json(INTENT_PROMPT + f"\nUser: {state.user_input}")
    intent = data.get("intent", "misc")

    # router says which node to go to next
    if intent == "habit_description":
        return {"next": "safety", "intent": intent}
    elif intent == "slip_report":
        return {"next": "slip", "intent": intent}
    
    return {"next": "coach", "intent": intent}



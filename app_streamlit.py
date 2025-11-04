import streamlit as st
from graphs import build_onboarding_graph

st.set_page_config(page_title="UnHabit AI", page_icon="🧠", layout="centered")

st.title("🧠 UnHabit AI Coach")
st.subheader("Break bad habits with an adaptive AI coach.")

# ---------- INIT SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    st.session_state.graph = build_onboarding_graph()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Session")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        if "full_21" in st.session_state:
            del st.session_state["full_21"]
        st.rerun()

    st.markdown("---")

    if "full_21" in st.session_state:
        st.markdown("### 🗓️ Full 21-Day Plan")
        plan = st.session_state.full_21
        for day, task in plan["daily_tasks"].items():
            st.markdown(f"**{day}** → {task}")

# ---------- CHAT DISPLAY ----------
st.markdown("### 💬 Conversation")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**🧑 You:**")
        st.markdown(msg["content"])
    else:
        # coach messages render cleanly WITHOUT prefix
        st.markdown(msg["content"])

st.markdown("---")

# ---------- STRUCTURED INPUT FORM ----------
st.markdown("### 🧾 Habit Details")

habit_category = st.selectbox(
    "Habit Category (required):",
    ["sexual_compulsion", "screen_addiction", "doomscrolling", "overeating", "nicotine", "gaming", "shopping_impulse", "other"]
)

peak_time = st.selectbox(
    "Peak Urge Time (required):",
    ["Morning", "Afternoon", "Evening", "Late Night", "Random/Unknown"]
)

location = st.selectbox(
    "Where does this usually happen? (required):",
    ["Bed", "Desk", "Sofa", "Bathroom", "Kitchen", "Workplace", "Outdoors", "Other/Unknown"]
)

emotion = st.selectbox(
    "Primary emotional trigger (required):",
    ["Boredom", "Stress", "Loneliness", "Anxiety", "Sadness", "Frustration", "Reward Seeking", "Unknown"]
)

secondary_emotion = st.multiselect(
    "Secondary emotions (optional):",
    ["Shame", "Anxiety", "Loneliness", "Frustration", "Numbness", "Curiosity"]
)

frequency = st.slider(
    "How often does this happen per week? (required):",
    min_value=1,
    max_value=50,
    value=5
)

# ---------- FREE-TEXT HABIT DESCRIPTION ----------
habit_input = st.text_area(
    "Describe your habit in your own words (required):",
    height=100,
    placeholder="Example: I relapse at night on my phone when I feel lonely…"
)

# ---------- SEND ----------
if st.button("Send"):
    if not habit_input.strip():
        st.warning("Please describe your habit above.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": habit_input})

    result = st.session_state.graph.invoke({
        "user_input": habit_input,
        "habit_category": habit_category,
        "peak_time": peak_time,
        "location": location,
        "emotion": emotion,
        "frequency": frequency,
        "secondary_emotion": secondary_emotion,
    })

    intent = result.get("intent", "misc")

    # ---------- SAFETY ----------
    safety = result.get("safety")
    if safety and safety.action == "block_and_escalate":
        st.session_state.messages.append({"role": "assistant", "content": safety.message})
        st.rerun()

    # ---------- SLIP ----------
    if intent == "slip_report":
        slip = result.get("slip_recovery")
        if slip:
            text = f"""
### 🛡 Slip Recovery Strategy
- Strategy: {slip.strategy}
- Next 24h Action: {slip.micro_action_24h}
- Environment Change: {slip.environment_change}
- Lesson Learned: {slip.lesson_learned}
- Replacement Action: {slip.replacement_action}
"""
            st.session_state.messages.append({"role": "assistant", "content": text})

        reply = result.get("coach_reply", "")
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # ---------- NORMAL FLOW ----------
    if intent == "habit_description":

        diagnostic = result.get("diagnostic")
        if diagnostic:
            text = f"""
### 🔍 Diagnostic
- Category: {diagnostic.habit_category}
- Primary Problem: {diagnostic.primary_problem}
- Risk Level: {diagnostic.risk_level}
- Time Triggers: {diagnostic.triggers.time}
- Location Triggers: {diagnostic.triggers.location}
- Emotional Triggers: {diagnostic.triggers.emotion}
"""
            st.session_state.messages.append({"role": "assistant", "content": text})

        pattern = result.get("pattern")
        if pattern:
            text = f"""
### 🧠 Behavior Pattern
- Peak Urge Time: {pattern.peak_time}
- Location Trigger: {pattern.location_trigger}
- Emotional Trigger: {pattern.emotional_trigger}
"""
            st.session_state.messages.append({"role": "assistant", "content": text})

        friction = result.get("friction")
        if friction:
            lines = "\n".join(f"- {h.description}" for h in friction.friction_habits)
            text = f"### 🚧 Environment Friction\n{lines}"
            st.session_state.messages.append({"role": "assistant", "content": text})

        replacement = result.get("replacement")
        if replacement:
            lines = "\n".join(f"- {alt}" for alt in replacement.alternatives)
            text = f"### ⚡ Replacement Dopamine\n{lines}"
            st.session_state.messages.append({"role": "assistant", "content": text})

        plan = result.get("plan")
        if plan:
            text = f"""
### ✅ Action Plan (Next 24–48h)
- Quick Win: {plan.quick_win}
- Tomorrow Task: {plan.tomorrow_task}
- Identity Reframe: {plan.identity_reframe}
"""
            st.session_state.messages.append({"role": "assistant", "content": text})

        plan21 = result.get("plan21")
        if plan21:
            tasks = list(plan21.daily_tasks.items())[:3]
            preview = "\n".join(f"- {k}: {v}" for k, v in tasks)

            text = f"""
### 📅 21-Day Plan (Preview)
- Phase: {plan21.phase_summary}

{preview}

(Full plan in sidebar ⬅️)
"""
            st.session_state.messages.append({"role": "assistant", "content": text})

            st.session_state.full_21 = plan21.model_dump()

        reply = result.get("coach_reply", "I'm here to help you.")
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # ---------- MISC ----------
    if intent == "misc":
        reply = result.get("coach_reply", "Tell me more about your habit.")
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

else:
    st.info("Fill details above, then click Send.")

st.markdown("---")
st.caption("Session persists until you clear it ✅")

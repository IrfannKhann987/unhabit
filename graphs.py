from langgraph.graph import StateGraph, START, END
from schemas import HabitState
from ai_nodes import (
    safety_node, diagnostic_node, plan_node, coach_node, plan21_node,
    pattern_analysis_node, friction_upgrade_node, replacement_dopamine_node, slip_recovery_node,intent_node
)


from langgraph.graph import StateGraph, END  # keep your existing imports

def build_onboarding_graph():
    graph = StateGraph(HabitState)

    # nodes
    graph.add_node("intent", intent_node)
    graph.add_node("safety", safety_node)
    graph.add_node("diagnostic", diagnostic_node)
    graph.add_node("pattern", pattern_analysis_node)
    graph.add_node("friction", friction_upgrade_node)
    graph.add_node("replacement", replacement_dopamine_node)
    graph.add_node("plan21", plan21_node)
    graph.add_node("slip", slip_recovery_node)
    graph.add_node("coach", coach_node)

    # entry
    graph.set_entry_point("intent")

    # === ROUTER: send flow based on intent_node's "next" value ===
    graph.add_conditional_edges(
        "intent",
        lambda s: s.next,  # returns one of the keys below
        {
            "safety": "safety",  # normal onboarding path
            "slip": "slip",      # relapse path
            "coach": "coach",    # misc/small-talk fallback
        },
    )

    # normal onboarding path
    graph.add_edge("safety", "diagnostic")
    graph.add_edge("diagnostic", "pattern")
    graph.add_edge("pattern", "friction")
    graph.add_edge("friction", "replacement")
    graph.add_edge("replacement", "plan21")
    graph.add_edge("plan21", "coach")

    # slip path
    graph.add_edge("slip", "coach")

    # finish
    graph.add_edge("coach", END)

    return graph.compile()

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.intent_agent import analyze_intent
from agents.scope_agent import analyze_scope
from agents.recovery_agent import analyze_recovery
from agents.report_agent import generate_final_report


class AgentState(TypedDict):
    repository_summary: dict
    commit_history: list
    file_histories: list
    evidence_map: list
    task_description: Optional[str]
    changed_files: Optional[list]

    intent_analysis: Optional[dict]
    scope_analysis: Optional[str]
    recovery_analysis: Optional[str]
    final_report: Optional[str]

def intent_node(state: AgentState):

    if not state["commit_history"]:
        return {
            "intent_analysis": {
                "likely_intent": "Unknown",
                "confidence": "LOW",
                "evidence": []
            }
        }

    result = analyze_intent(
        state["commit_history"][0],
        state["file_histories"],
        state["evidence_map"]
    )

    return {
        "intent_analysis": result
    }

def scope_node(state: AgentState):

    task = state.get("task_description")
    changed_files = state.get("changed_files")

    if not task or not changed_files:
        return {
            "scope_analysis":
            "Scope analysis skipped because no task or changed files were provided."
        }

    result = analyze_scope(
        task,
        changed_files
    )

    return {
        "scope_analysis": result
    }

def recovery_node(state: AgentState):

    repository_data = {
        "repository_summary":
        state["repository_summary"],

        "recent_commits":
        state["commit_history"]
    }

    result = analyze_recovery(
        repository_data
    )

    return {
        "recovery_analysis": result
    }

def report_node(state: AgentState):

    result = generate_final_report(
        state["repository_summary"],
        state["intent_analysis"],
        state["scope_analysis"],
        state["recovery_analysis"]
    )

    return {
        "final_report": result
    }

def route_after_intent(state: AgentState):

    commit_count = len(
        state.get("commit_history", [])
    )

    # Not enough history
    if commit_count < 2:
        return "recovery_agent"

    # Check if scope analysis is possible
    if (
        state.get("task_description")
        and state.get("changed_files")
    ):
        return "scope_agent"

    return "recovery_agent"

def create_workflow():

    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node(
        "intent_agent",
        intent_node
    )

    workflow.add_node(
        "scope_agent",
        scope_node
    )

    workflow.add_node(
        "recovery_agent",
        recovery_node
    )

    workflow.add_node(
        "report_agent",
        report_node
    )

    # Start workflow
    workflow.set_entry_point(
        "intent_agent"
    )

    # Agent flow
    workflow.add_conditional_edges(
        "intent_agent",
        route_after_intent,
        {
            "scope_agent": "scope_agent",
            "recovery_agent": "recovery_agent"
        }
    )

    workflow.add_edge(
        "scope_agent",
        "recovery_agent"
    )

    workflow.add_edge(
        "recovery_agent",
        "report_agent"
    )

    workflow.add_edge(
        "report_agent",
        END
    )

    return workflow.compile()


agent_workflow = create_workflow()

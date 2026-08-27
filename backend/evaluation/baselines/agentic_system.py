import sys
import os

# Add backend to path so we can import graph
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from graph.workflow import agent_workflow

def agentic_system(state):
    try:
        result = agent_workflow.invoke(state)

        return {
            "prediction": result.get("intent_analysis"),
            "method": "Agentic Code Archaeology"
        }
    except Exception as e:
        return {
            "prediction": str(e),
            "method": "Agentic Code Archaeology"
        }

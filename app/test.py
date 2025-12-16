from tools import stub_evidence
from graph import build_graph
from langchain_core.messages import HumanMessage

# Direct test
print("=" * 60)
print("DIRECT STUB EVIDENCE TEST")
print("=" * 60)
result = stub_evidence("Evaluate pembrolizumab for melanoma")
print(result)

# Full graph test with stub evidence only
print("\n" + "=" * 60)
print("FULL GRAPH TEST (forcing stub_evidence)")
print("=" * 60)

# Temporarily modify TOOLS to only use stub
import graph
original_tools = graph.TOOLS
graph.TOOLS = [graph.stub_evidence_tool]  # Only stub

try:
    test_graph = build_graph()
    test_query = "Evaluate pembrolizumab for melanoma"
    
    result = test_graph.invoke({
        "messages": [HumanMessage(content=test_query)],
        "user_query": test_query,
        "tool_loops": 0,
    })
    
    print("\nDECISION BRIEF:")
    print("-" * 60)
    print(result.get("decision_brief", "No brief generated"))
    
finally:
    # Restore original tools
    graph.TOOLS = original_tools

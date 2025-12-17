"""
Test graph generation tools without hitting API rate limits
"""
from tools import generate_graph_dot, render_dot_to_png_base64

# Test Tool 6: generate_graph_dot
print("=" * 60)
print("Testing Tool 6: generate_graph_dot")
print("=" * 60)

nodes = [
    {"id": "start", "label": "START"},
    {"id": "preprocess", "label": "Preprocess Query"},
    {"id": "llm", "label": "LLM Call"},
    {"id": "tools", "label": "Tool Execution"},
    {"id": "synthesize", "label": "Synthesize Brief"},
    {"id": "end", "label": "END"},
]

edges = [
    {"from": "start", "to": "preprocess"},
    {"from": "preprocess", "to": "llm"},
    {"from": "llm", "to": "tools", "label": "needs tools"},
    {"from": "tools", "to": "llm", "label": "loop"},
    {"from": "llm", "to": "synthesize", "label": "done"},
    {"from": "synthesize", "to": "end"},
]

dot_code = generate_graph_dot(
    title="PharmAI Navigator Workflow",
    nodes=nodes,
    edges=edges,
    rankdir="TB"
)

print("\nGenerated DOT code:")
print(dot_code)

# Test Tool 8: render_dot_to_png_base64
print("\n" + "=" * 60)
print("Testing Tool 8: render_dot_to_png_base64")
print("=" * 60)

result = render_dot_to_png_base64(dot_code)

if result.get("ok"):
    png_b64 = result["png_base64"]
    print(f"\nPNG generated successfully!")
    print(f"Base64 length: {len(png_b64)} characters")
    print(f"First 100 chars: {png_b64[:100]}...")
    
    # Optionally save to file
    import base64
    with open("pharmai_workflow.png", "wb") as f:
        f.write(base64.b64decode(png_b64))
    print("\nSaved to pharmai_workflow.png")
else:
    print(f"\n✗ PNG generation failed: {result.get('error')}")
    print("\nNote: You may need to install graphviz:")
    print("  pip install graphviz")
    print("  And install system binaries: https://graphviz.org/download/")

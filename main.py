from onboard_agent import config
from onboard_agent.database.postgres import init_db
from onboard_agent.graph.build_graph import build_graph

if __name__ == "__main__":
    if not config.ANTHROPIC_API_KEY:
        print("Set ANTHROPIC_API_KEY before running.")
    else:
        init_db()
        graph = build_graph()

        question = "What's John Smith's email and who is his manager?"
        result = graph.invoke({"messages": [{"role": "user", "content": question}]})
        print(result["messages"][-1].content)

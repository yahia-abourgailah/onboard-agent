from onboard_agent.config import Settings
from onboard_agent.database.postgres import init_db
from onboard_agent.graph.build_graph import invoke_graph

if __name__ == "__main__":
    settings = Settings()
    if not settings.OPENAI_API_KEY:
        print("Set OPENAI_API_KEY before running.")
    else:
        init_db()

        question = "What's John Smith's email and who is his manager?"
        result = invoke_graph(question)
        print(result["messages"][-1].content)

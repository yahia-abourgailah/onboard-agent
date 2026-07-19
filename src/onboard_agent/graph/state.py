from langgraph.graph import MessagesState


class AgentState(MessagesState):
    files_uploaded: bool
    laptop_received: bool

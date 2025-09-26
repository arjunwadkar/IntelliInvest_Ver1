from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 1. Define a simple state (dictionary to carry data)
class AgentState(dict):
    pass

# 2. Initialize ChatGPT model
llm = ChatOpenAI(model="gpt-4o-mini")  # you can use gpt-4o or gpt-3.5-turbo too

# 3. Define a node function
def chatgpt_node(state: AgentState):
    user_message = state.get("user_message")
    response = llm.invoke(user_message)   # Call ChatGPT
    state["assistant_response"] = response.content
    return state

# 4. Build the graph
graph = StateGraph(AgentState)
graph.add_node("chatgpt", chatgpt_node)   # add the node
graph.set_entry_point("chatgpt")          # start here
graph.add_edge("chatgpt", END)            # go to END after node

# 5. Compile the graph
app = graph.compile()

# 6. Run the agent
if __name__ == "__main__":
    user_input = "Hello! Can you tell me a fun fact about space?"
    output = app.invoke({"user_message": user_input})
    print("Assistant:", output["assistant_response"])
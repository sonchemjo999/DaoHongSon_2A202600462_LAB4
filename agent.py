from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import search_flights, search_hotels, calculate_budget, get_cache_stats, cache_clear
from logger import SessionLogger
from dotenv import load_dotenv

load_dotenv()

# 1. Đọc System Prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 3. Khởi tạo LLM và Tools
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-5.4")
llm_with_tools = llm.bind_tools(tools_list)

# Logger — khởi tạo khi chạy main
session_logger: SessionLogger | None = None
agent_step = 0


# 4. Agent Node
def agent_node(state: AgentState) -> dict:
    global agent_step
    agent_step += 1

    messages = state["messages"]

    # Đảm bảo system prompt luôn ở đầu
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # === LOGGING ===
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"  🔧 Gọi tool: {tc['name']}({tc['args']})")
            if session_logger:
                session_logger.log_tool_call(tc["name"], tc["args"], agent_step)
    else:
        print(f"  💬 Trả lời trực tiếp")

    # Log LLM metrics (tokens)
    if session_logger:
        session_logger.log_llm_metric(response, agent_step)

    return {"messages": [response]}


# 5. Xây dựng Graph với Checkpointer (nhớ hội thoại)
builder = StateGraph(AgentState)

# Thêm nodes
builder.add_node("agent", agent_node)
tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# Khai báo edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

# Compile graph với MemorySaver
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


# 6. Chat loop
if __name__ == "__main__":
    print("=" * 60)
    print("  TravelBuddy — Trợ lý Du lịch Thông minh")
    print("  Gõ 'quit' để thoát | 'cache' xem | 'clear' xóa cache")
    print("=" * 60)

    # Khởi tạo logger cho session này
    session_logger = SessionLogger(model="gpt-4o-mini")
    print(f"  📝 Session: {session_logger.session_id}")

    # thread_id giữ nguyên trong suốt phiên → agent nhớ toàn bộ hội thoại
    config = {"configurable": {"thread_id": "user_session_1"}}

    while True:
        user_input = input("\nBạn: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("Cảm ơn bạn đã sử dụng TravelBuddy! Chúc bạn có chuyến đi vui vẻ! 👋")
            session_logger.log_session_end()
            break

        if user_input.lower() == "cache":
            print(f"\n{get_cache_stats()}")
            continue

        if user_input.lower().startswith("clear"):
            keyword = user_input[5:].strip()
            print(f"\n{cache_clear(keyword)}")
            continue

        if not user_input:
            continue

        print("\nTravelBuddy đang suy nghĩ...")

        # Log query start
        agent_step = 0
        query_start = session_logger.log_agent_start(user_input)

        result = graph.invoke({"messages": [("human", user_input)]}, config=config)
        final = result["messages"][-1]
        print(f"\nTravelBuddy: {final.content}")

        # Log response
        session_logger.log_agent_response(final.content, query_start, agent_step)

import json
import os
import time
import uuid
from datetime import datetime


LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


class SessionLogger:
    """
    Ghi logs theo session — mỗi phiên chat = 1 cặp file:
      - session_agent_YYYY-MM-DDTHH-MM-SS.json   (tổng kết session)
      - session_agent_YYYY-MM-DDTHH-MM-SS.jsonl   (events theo dòng, realtime)
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.session_id = f"sess_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        self.model = model
        self.start_time = int(time.time() * 1000)
        self.events: list[dict] = []
        self.total_tokens = 0
        self.total_tool_calls = 0
        self.total_queries = 0

        # Tên file theo timestamp
        ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        self.json_path = os.path.join(LOGS_DIR, f"session_agent_{ts}.json")
        self.jsonl_path = os.path.join(LOGS_DIR, f"session_agent_{ts}.jsonl")

        # Ghi event bắt đầu session
        self._log_event("SESSION_START", {
            "session_id": self.session_id,
            "model": self.model,
        })

    def _now_iso(self) -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}Z"

    def _log_event(self, event: str, data: dict) -> None:
        entry = {
            "timestamp": self._now_iso(),
            "event": event,
            "data": data,
        }
        self.events.append(entry)

        # Ghi JSONL realtime (mỗi event 1 dòng)
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_agent_start(self, query: str) -> float:
        """Ghi event khi user gửi query. Trả về start_time để tính latency."""
        self.total_queries += 1
        self._log_event("AGENT_START", {
            "session_id": self.session_id,
            "query": query,
            "model": self.model,
        })
        return time.time()

    def log_tool_call(self, tool_name: str, tool_args: dict, step: int) -> None:
        """Ghi event khi agent gọi tool."""
        self.total_tool_calls += 1
        self._log_event("TOOL_CALL", {
            "step": step,
            "tool_name": tool_name,
            "tool_args": tool_args,
        })

    def log_llm_metric(self, response, step: int) -> None:
        """Ghi metrics từ LLM response (tokens, latency...)."""
        usage = {}
        if hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        self.total_tokens += total_tokens

        self._log_event("LLM_METRIC", {
            "step": step,
            "model": self.model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "function_call_count": len(response.tool_calls) if response.tool_calls else 0,
        })

    def log_agent_response(self, answer: str, start_time: float, step: int) -> None:
        """Ghi event khi agent trả lời xong."""
        latency_ms = int((time.time() - start_time) * 1000)
        self._log_event("AGENT_RESPONSE", {
            "step": step,
            "answer_preview": answer[:200] if answer else "",
            "latency_ms": latency_ms,
        })

    def log_session_end(self) -> None:
        """Ghi tổng kết session ra file JSON."""
        total_duration_ms = int(time.time() * 1000) - self.start_time
        self._log_event("SESSION_END", {
            "total_duration_ms": total_duration_ms,
            "total_queries": self.total_queries,
            "total_tokens": self.total_tokens,
            "total_tool_calls": self.total_tool_calls,
        })

        # Ghi file JSON tổng kết
        summary = {
            "session_id": self.session_id,
            "label": "agent",
            "model": self.model,
            "start_time": self.start_time,
            "total_duration_ms": total_duration_ms,
            "total_queries": self.total_queries,
            "total_tokens": self.total_tokens,
            "total_tool_calls": self.total_tool_calls,
            "events": self.events,
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n📝 Logs đã lưu:")
        print(f"  {self.jsonl_path}")
        print(f"  {self.json_path}")

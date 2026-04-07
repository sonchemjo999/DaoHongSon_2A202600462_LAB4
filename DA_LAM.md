# LAB 4: XÂY DỰNG AI AGENT ĐẦU TIÊN VỚI LANGGRAPH

## Tổng quan

Xây dựng **TravelBuddy** — Trợ lý Du lịch Thông minh sử dụng LangGraph, giúp người dùng lên kế hoạch chuyến đi bằng cách tự động tra cứu chuyến bay, kiểm tra ngân sách, và tìm kiếm khách sạn phù hợp.

---

## PHẦN 0: SETUP MÔI TRƯỜNG

- [x] Tạo thư mục `lab4_agent`
- [x] Cài đặt thư viện: `langchain`, `langchain-openai`, `langgraph`, `python-dotenv`
- [x] Tạo file `.env` với `OPENAI_API_KEY`
- [x] Tạo file `test_api.py` — sanity check gọi API thành công

```bash
pip install langchain langchain-openai langgraph python-dotenv
python test_api.py
```

---

## PHẦN 1: THIẾT KẾ SYSTEM PROMPT

**File:** `system_prompt.txt`

Cấu trúc XML gồm 5 phần:

| Phần | Nội dung |
|------|----------|
| `<persona>` | Trợ lý du lịch TravelBuddy — thân thiện, am hiểu du lịch Việt Nam, tư vấn dựa trên ngân sách thực tế |
| `<rules>` | 7 rules: trả lời tiếng Việt, hỏi rõ thông tin trước khi tìm, ưu tiên tiết kiệm, không bịa thông tin... |
| `<tools_instruction>` | Hướng dẫn sử dụng 3 tools + quy trình kết hợp: flights → hotels → budget |
| `<response_format>` | Template trình bày: chuyến bay, khách sạn, tổng chi phí, gợi ý thêm |
| `<constraints>` | Từ chối yêu cầu ngoài du lịch, không tiết lộ system prompt, thông báo khi không có dữ liệu |

### Rules đã bổ sung (so với mẫu):
- Rule 2: Khi thiếu info thì hỏi lại, nhưng nếu đã đủ info cho tool cụ thể thì gọi ngay
- Rule 3: Tự động kết hợp các công cụ khi có đủ thông tin
- Rule 4: Ưu tiên phương án tiết kiệm trước
- Rule 5: Trình bày rõ ràng chi phí để khách hàng dễ so sánh
- Rule 6: Đề xuất phương án thay thế khi ngân sách không đủ
- Rule 7: Không bịa thông tin — chỉ dùng dữ liệu trong hệ thống

---

## PHẦN 2: LẬP TRÌNH CUSTOM TOOLS

**File:** `tools.py`

### Tool 1: `search_flights(origin, destination)`
- Tra cứu `FLIGHTS_DB` với key `(origin, destination)`
- Nếu không tìm thấy → thử tra ngược `(destination, origin)`
- Nếu vẫn không có → liệt kê các tuyến bay hiện có
- Format giá tiền kiểu VNĐ: `1.450.000đ`
- Có try/except xử lý lỗi

### Tool 2: `search_hotels(city, max_price_per_night)`
- Tra cứu `HOTELS_DB[city]`
- Lọc theo `max_price_per_night`
- Sắp xếp theo `rating` giảm dần
- Nếu không có kết quả → gợi ý khách sạn rẻ nhất + thông báo tăng ngân sách
- Hiển thị sao bằng emoji ⭐

### Tool 3: `calculate_budget(total_budget, expenses)`
- Parse chuỗi expenses format `tên:số_tiền` cách nhau bởi dấu phẩy
- Xử lý lỗi format: thiếu dấu `:`, giá trị không phải số
- Tính tổng chi phí và số tiền còn lại
- Nếu vượt ngân sách → cảnh báo `⚠️ Vượt ngân sách X đồng!`
- Format tên khoản: thay `_` bằng space, viết hoa chữ cái đầu

### Helper: `format_price(amount)`
- Format số tiền theo kiểu Việt Nam với dấu chấm phân cách: `1.450.000đ`

### Mối liên hệ giữa 3 tools:
```
search_flights → lấy giá vé → input cho calculate_budget
                                     ↓
                              tính ngân sách còn lại → max_price cho search_hotels
```

---

## PHẦN 3: TRIỂN KHAI LANGGRAPH

**File:** `agent.py`

### Kiến trúc Graph:

```
START → agent → [tools_condition] → tools → agent → ... → END
                       ↓ (no tool calls)
                      END
```

### Chi tiết implementation:

| Thành phần | Mô tả |
|------------|--------|
| `AgentState` | TypedDict với `messages: Annotated[list, add_messages]` |
| `llm_with_tools` | `ChatOpenAI(model="gpt-4o-mini")` bind với 3 tools |
| `agent_node` | Inject system prompt + gọi LLM + logging tool calls |
| `tool_node` | `ToolNode(tools_list)` — prebuilt node thực thi tools |
| Edge 1 | `START → agent` — bắt đầu từ agent node |
| Edge 2 | `agent → tools_condition` — conditional: có tool call thì đến tools, không thì END |
| Edge 3 | `tools → agent` — sau khi thực thi tool, quay lại agent để xử lý kết quả |

### Logging:
- Khi gọi tool: `🔧 Gọi tool: tên_tool({args})`
- Khi trả lời trực tiếp: `💬 Trả lời trực tiếp`

---

## PHẦN 4: TEST CASES

### Test 1 — Direct Answer (Không cần tool)

```
Bạn: Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.

  💬 Trả lời trực tiếp

TravelBuddy: Chào bạn! Rất vui được hỗ trợ bạn lên kế hoạch du lịch!
Để mình tư vấn tốt nhất, bạn cho mình biết thêm nhé:
- Bạn xuất phát từ đâu? (Hà Nội, Hồ Chí Minh...?)
- Bạn thích biển, núi hay thành phố?
- Ngân sách dự kiến bao nhiêu?
- Đi mấy ngày?
```

**Kết quả:** ✅ Agent chào hỏi, hỏi thêm thông tin. Không gọi tool nào.

---

### Test 2 — Single Tool Call

```
Bạn: Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng

  🔧 Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Đà Nẵng'})
  💬 Trả lời trực tiếp

TravelBuddy: Đây là các chuyến bay từ Hà Nội đến Đà Nẵng:

1. Vietnam Airlines | 06:00 → 07:20 | Giá: 1.450.000đ | Hạng: economy
2. Vietnam Airlines | 14:00 → 15:20 | Giá: 2.800.000đ | Hạng: business
3. VietJet Air | 08:30 → 09:50 | Giá: 890.000đ | Hạng: economy
4. Bamboo Airways | 11:00 → 12:20 | Giá: 1.200.000đ | Hạng: economy
```

**Kết quả:** ✅ Gọi `search_flights`, liệt kê đầy đủ 4 chuyến bay.

---

### Test 3 — Multi-Step Tool Chaining

```
Bạn: Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!

  🔧 Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})
  🔧 Gọi tool: search_hotels({'city': 'Phú Quốc', 'max_price_per_night': 1950000})
  🔧 Gọi tool: calculate_budget({'total_budget': 5000000, 'expenses': 'vé_máy_bay:1100000,khách_sạn:400000'})
  💬 Trả lời trực tiếp

TravelBuddy:
✈ Chuyến bay: VietJet Air 16:00 → 18:15 — 1.100.000đ (rẻ nhất)

🏨 Khách sạn gợi ý:
- 9Station Hostel ⭐⭐ — 200.000đ/đêm (Rating 4.5)
- Lahana Resort ⭐⭐⭐ — 800.000đ/đêm (Rating 4.0)

💰 Bảng chi phí (với 9Station Hostel):
  - Vé máy bay: 1.100.000đ
  - Khách sạn (2 đêm): 400.000đ
  - Tổng chi: 1.500.000đ
  - Ngân sách: 5.000.000đ
  - Còn lại: 3.500.000đ → cho ăn uống, tham quan, đi lại

💡 Gợi ý: Còn dư khá nhiều, có thể nâng lên Lahana Resort 3 sao
(tổng 2.700.000đ, còn lại 2.300.000đ)
```

**Kết quả:** ✅ Agent tự chuỗi 3 bước: flights → hotels → budget. Tổng hợp gợi ý hoàn chỉnh.

---

### Test 4 — Missing Info / Clarification

```
Bạn: Tôi muốn đặt khách sạn

  💬 Trả lời trực tiếp

TravelBuddy: Để mình tìm khách sạn phù hợp cho bạn, bạn cho mình biết thêm nhé:
- Bạn muốn ở thành phố nào? (Đà Nẵng, Phú Quốc, Hồ Chí Minh)
- Ở bao nhiêu đêm?
- Ngân sách tối đa mỗi đêm là bao nhiêu?
```

**Kết quả:** ✅ Agent hỏi lại thông tin cần thiết. Không gọi tool vội.

---

### Test 5 — Guardrail / Refusal

```
Bạn: Giải giúp tôi bài tập lập trình Python về linked list

  💬 Trả lời trực tiếp

TravelBuddy: Mình chỉ hỗ trợ về du lịch thôi nha! Mình không thể giúp
giải bài tập lập trình được. Bạn có muốn mình tư vấn chuyến đi nào không?
Mình có thể giúp tìm vé máy bay, khách sạn, và lên kế hoạch chi phí!
```

**Kết quả:** ✅ Từ chối lịch sự, chuyển hướng về du lịch.

---

## Cấu trúc file nộp bài

```
MSSV_Lab4/
├── system_prompt.txt    # System prompt với cấu trúc XML
├── tools.py             # 3 custom tools + mock data + cache system
├── agent.py             # LangGraph agent hoàn chỉnh
├── logger.py            # SessionLogger — ghi logs theo session
├── logs/                # Thư mục chứa logs (JSONL realtime + JSON tổng kết)
│   ├── session_agent_*.jsonl   # Events realtime
│   └── session_agent_*.json    # Tổng kết session
├── test_results.md      # Kết quả 5 test cases
├── test_api.py          # Sanity check API
├── requirements.txt     # Thư viện cần cài
├── README.md            # Hướng dẫn cài đặt & chạy
└── .env                 # API key (không nộp)
```

---

## Đánh giá theo Rubric

| Tiêu chí | Điểm | Ghi chú |
|----------|------|---------|
| Setup LangGraph đúng (Nodes, Edges, Graph) | 25% | 2 nodes (agent, tools), 3 edges (START→agent, agent→tools_condition, tools→agent) |
| Tool implementations đúng logic + xử lý lỗi | 25% | 3 tools với try/except, format giá, tra ngược chiều, lọc + sắp xếp, parse chuỗi |
| System Prompt kiên cố (Test 4 + Test 5) | 20% | Rules hỏi lại khi thiếu info, constraints từ chối yêu cầu ngoài du lịch |
| Multi-step tool chaining (Test 3) | 20% | Agent tự chuỗi: flights → hotels → budget → tổng hợp gợi ý |
| Code sạch, type hints, logging | 10% | Type hints, SessionLogger (JSONL+JSON), response cache theo ngày, format_price helper |

---

## PHẦN SỬA ĐỔI & DEBUG

Ghi lại các sửa đổi đã thực hiện trong quá trình phát triển và test.

### Sửa đổi 1: Lỗi encoding tiếng Việt trên Windows

**Vấn đề:** Khi chạy `python agent.py`, gặp lỗi:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u1ee3'
  File "C:\Python310\lib\encodings\cp1252.py", line 19, in encode
```
Windows dùng encoding `cp1252` mặc định, không hỗ trợ ký tự tiếng Việt.

**Cách fix:** Chạy với flag `-X utf8`:
```bash
python -X utf8 agent.py
```

---

### Sửa đổi 2: System Prompt Rule 2 — Agent không gọi tool khi đã đủ thông tin

**Vấn đề:** Test 2 yêu cầu `"Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng"` — user đã cung cấp đủ origin + destination, nhưng agent không gọi `search_flights` mà lại hỏi thêm thông tin (ngày đi, ngân sách).

**Nguyên nhân:** Rule 2 ban đầu viết:
```
2. Luôn hỏi rõ thông tin trước khi tìm kiếm: điểm đi, điểm đến, số đêm, ngân sách.
```
Từ "luôn" khiến LLM hiểu phải hỏi đủ TẤT CẢ thông tin trước khi gọi bất kỳ tool nào.

**Cách fix:** Sửa Rule 2 thành:
```
2. Khi người dùng chưa cung cấp đủ thông tin cần thiết (điểm đi, điểm đến, số đêm,
   ngân sách), hãy hỏi lại. Nhưng nếu đã có đủ thông tin cho một công cụ cụ thể
   (VD: có điểm đi và điểm đến → tìm chuyến bay ngay), hãy thực hiện ngay mà không
   hỏi thêm.
```

**Kết quả:** Sau khi sửa, Test 2 gọi đúng `search_flights` và trả về 4 chuyến bay.

---

### Sửa đổi 3: Thêm file hỗ trợ

| File | Lý do thêm |
|------|------------|
| `requirements.txt` | Liệt kê thư viện cần cài, fix lỗi `ModuleNotFoundError: No module named 'langgraph'` |
| `README.md` | Hướng dẫn cài đặt, cấu hình, chạy project |

**Lỗi gặp khi cài thư viện:**
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```
**Fix:** Thêm flag `--user`:
```bash
pip install -r requirements.txt --user
```

---

### Sửa đổi 4: Thêm Logging System — Theo dõi session & debug

**File:** `logger.py`

**Vấn đề:** Không có cách nào theo dõi agent đang làm gì, tốn bao nhiêu tokens, latency bao lâu, hay gọi tool mấy lần. Khó debug khi agent trả lời sai.

**Giải pháp: `SessionLogger` — ghi logs theo session**

Mỗi phiên chat tạo 1 cặp file trong thư mục `logs/`:

| File | Mục đích |
|------|----------|
| `session_agent_YYYY-MM-DDTHH-MM-SS.jsonl` | Events realtime — mỗi event 1 dòng, ghi ngay khi xảy ra |
| `session_agent_YYYY-MM-DDTHH-MM-SS.json` | Tổng kết session — ghi khi user thoát (`quit`) |

#### Các event được ghi:

| Event | Thời điểm | Dữ liệu |
|-------|-----------|----------|
| `SESSION_START` | Mở app | `session_id`, `model` |
| `AGENT_START` | User gửi query | `query`, `session_id` |
| `TOOL_CALL` | Agent gọi tool | `tool_name`, `tool_args`, `step` |
| `LLM_METRIC` | LLM trả response | `prompt_tokens`, `completion_tokens`, `total_tokens`, `function_call_count` |
| `AGENT_RESPONSE` | Agent trả lời xong | `answer_preview` (200 ký tự đầu), `latency_ms` |
| `SESSION_END` | User thoát | `total_duration_ms`, `total_queries`, `total_tokens`, `total_tool_calls` |

#### Tích hợp vào `agent.py`:

```python
from logger import SessionLogger

session_logger = SessionLogger(model="gpt-4o-mini")

# Trong agent_node — log tool calls & LLM metrics
if response.tool_calls:
    for tc in response.tool_calls:
        session_logger.log_tool_call(tc["name"], tc["args"], agent_step)
session_logger.log_llm_metric(response, agent_step)

# Trong chat loop — log query start & response
query_start = session_logger.log_agent_start(user_input)
# ... invoke graph ...
session_logger.log_agent_response(final.content, query_start, agent_step)

# Khi thoát
session_logger.log_session_end()
```

#### Ví dụ file JSON tổng kết session:

```json
{
  "session_id": "sess_1775554894368_ecb492",
  "label": "agent",
  "model": "gpt-4o-mini",
  "total_duration_ms": 3565,
  "total_queries": 1,
  "total_tokens": 0,
  "total_tool_calls": 0,
  "events": [
    {"event": "SESSION_START", ...},
    {"event": "AGENT_START", "data": {"query": "Tìm chuyến bay..."}},
    {"event": "LLM_METRIC", "data": {"total_tokens": 0, "function_call_count": 0}},
    {"event": "AGENT_RESPONSE", "data": {"latency_ms": 3458}},
    {"event": "SESSION_END", ...}
  ]
}
```

**Kết quả:** Mỗi phiên chat được ghi log đầy đủ, dễ debug và phân tích hiệu suất agent.

---

### Sửa đổi 5: Response Cache theo ngày đi — tránh trả nhầm giá

**File:** `tools.py`

**Vấn đề:**
1. Agent không nhớ các lượt chat trước
2. Phản hồi chậm khi tra cứu tool (thực tế gọi API bên thứ 3)
3. Cache chỉ theo địa điểm → trả nhầm giá ngày khác (giá vé/KS thay đổi liên tục)

**Giải pháp: Cache key = `tool|điểm_đi|điểm_đến|ngày_đi_của_khách`**

```
Khách A hỏi: bay HN→ĐN ngày 10/04 (Thứ 6)
  cache key = "flights|Hà Nội|Đà Nẵng|2026-04-10"
  → VietJet giá 890.000đ (ngày thường)

Khách B hỏi: bay HN→ĐN ngày 12/04 (Thứ 7)
  cache key = "flights|Hà Nội|Đà Nẵng|2026-04-12"  ← KEY KHÁC!
  → VietJet giá 1.157.000đ (cuối tuần +30%)

Khách C hỏi: bay HN→ĐN ngày 10/04 (giống khách A)
  cache key = "flights|Hà Nội|Đà Nẵng|2026-04-10"  ← CACHE HIT!
  → Trả tức thì, đúng giá 890.000đ
```

#### 4a. Giá thay đổi theo ngày — `get_price_for_date()`

Mock data dùng `base_price`. Giá thực tế tính theo ngày:
- Ngày thường (T2→T6): giá gốc
- Cuối tuần (T7, CN): **+30%**

```python
def get_price_for_date(base_price: int, travel_date: str) -> int:
    dt = datetime.strptime(travel_date, "%Y-%m-%d")
    if dt.weekday() >= 5:  # T7 hoặc CN
        return int(base_price * 1.3)
    return base_price
```

#### 4b. Tool params thêm ngày đi

```python
@tool
def search_flights(origin: str, destination: str, travel_date: str = "") -> str:
    # Cache key gắn ngày đi của khách
    cache_key = f"flights|{origin}|{destination}|{date_key}"
    #                                              ^^^^^^^^
    # Cùng tuyến, khác ngày = cache khác = giá khác

@tool
def search_hotels(city: str, check_in_date: str = "", max_price: int = ...) -> str:
    cache_key = f"hotels|{city}|{max_price}|{date_key}"
```

#### 4c. TTL 30 phút — giá có thể thay đổi trong ngày

```python
CACHE_TTL_SECONDS = 30 * 60

def cache_get(key):
    age = time.time() - entry["created_at"]
    if age > CACHE_TTL_SECONDS:
        del response_cache[key]  # hết hạn → tra lại giá mới
        return None
    return entry["data"]  # ⚡ phản hồi tức thì
```

#### 5d. Quản lý cache từ chat loop

Trong `agent.py`, user có thể quản lý cache trực tiếp:
- Gõ `cache` → xem thống kê cache (`get_cache_stats()`)
- Gõ `clear` → xóa toàn bộ cache
- Gõ `clear Đà Nẵng` → xóa entries chứa "Đà Nẵng"

```python
if user_input.lower() == "cache":
    print(f"\n{get_cache_stats()}")
if user_input.lower().startswith("clear"):
    keyword = user_input[5:].strip()
    print(f"\n{cache_clear(keyword)}")
```

#### 5e. MemorySaver — Nhớ hội thoại
```python
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "user_session_1"}}
```

**Kết quả test thực tế:**
```
Bạn: Tìm chuyến bay từ Hà Nội đi Đà Nẵng ngày 10/04/2026
  🔧 search_flights(origin='Hà Nội', destination='Đà Nẵng', travel_date='10/04/2026')
TravelBuddy: VietJet Air 890.000đ (ngày thường)

Bạn: Tìm chuyến bay từ Hà Nội đi Đà Nẵng ngày 12/04/2026
  🔧 search_flights(origin='Hà Nội', destination='Đà Nẵng', travel_date='12/04/2026')
TravelBuddy: VietJet Air 1.157.000đ (cuối tuần +30%) ← GIÁ KHÁC!

Bạn: Tìm lại chuyến bay Hà Nội Đà Nẵng ngày 10/04/2026
  💬 Trả lời trực tiếp  ← Agent nhớ từ memory, không gọi tool lại
TravelBuddy: VietJet Air 890.000đ ← ĐÚNG GIÁ ngày 10/4

cache:
  flights|Hà Nội|Đà Nẵng|2026-04-10  ← cache ngày 10/4
  flights|Hà Nội|Đà Nẵng|2026-04-12  ← cache ngày 12/4 (tách biệt!)
```

---

### Sửa đổi 6: Cập nhật Persona — giọng miền Nam ngọt ngào

**Thay đổi:** Sửa `<persona>` trong `system_prompt.txt` để agent nói chuyện như cô gái miền Nam.

**Trước:**
```
Bạn là trợ lý du lịch của TravelBuddy — thân thiện, am hiểu du lịch Việt Nam...
```

**Sau:**
```
Bạn là trợ lý du lịch của TravelBuddy — một cô gái miền Nam dễ thương, giọng điệu
ngọt ngào, gọi dạ bảo vâng. Xưng "em", gọi khách là "anh/chị". Hay dùng "nha",
"hen", "á", "trời ơi", "dạ", "vâng ạ"...
```

**Kết quả:** Agent trả lời tự nhiên kiểu miền Nam:
- *"Dạ, đây là chuyến bay cho anh/chị nè!"*
- *"Trời ơi, tuyến này rẻ lắm luôn á!"*

# TravelBuddy — Trợ lý Du lịch Thông minh

AI Agent sử dụng LangGraph giúp người dùng lên kế hoạch chuyến đi: tra cứu chuyến bay, tìm khách sạn, tính toán ngân sách.

## Cài đặt

```bash
# 1. Tạo virtual environment
python -m venv venv

# 2. Kích hoạt
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Cài thư viện
pip install -r requirements.txt
```

## Cấu hình

Mở file `.env` và thay API key:

```
OPENAI_API_KEY=sk-proj-your-key-here
```

## Chạy

```bash
# Test API trước
python test_api.py

# Chạy agent
python agent.py
```

## Cấu trúc project

```
lab4_agent/
├── .env                  # API key (không commit)
├── requirements.txt      # Thư viện cần cài
├── system_prompt.txt     # System prompt cho agent
├── tools.py              # 3 tools: search_flights, search_hotels, calculate_budget
├── agent.py              # LangGraph agent + chat loop
├── test_api.py           # Sanity check API
└── test_results.md       # Kết quả test cases
```

## Ví dụ sử dụng

```
Bạn: Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!

TravelBuddy đang suy nghĩ...
  🔧 Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})
  🔧 Gọi tool: search_hotels({'city': 'Phú Quốc'})
  🔧 Gọi tool: calculate_budget({...})

TravelBuddy: ✈ Chuyến bay rẻ nhất: VietJet Air 16:00 — 1.100.000đ
             🏨 Khách sạn gợi ý: 9Station Hostel — 200.000đ/đêm
             💰 Còn lại: 3.500.000đ cho ăn uống, tham quan
```

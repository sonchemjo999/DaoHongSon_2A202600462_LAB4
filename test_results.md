## KẾT QUẢ TEST CASES

### Test 1 — Direct Answer (Không cần tool)

**Input:** `Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.`

**Console log:**
```
💬 Trả lời trực tiếp
```

**Kỳ vọng:** Agent chào hỏi, hỏi thêm về sở thích/ngân sách/thời gian. Không gọi tool nào.

**Kết quả:** ✅ PASS — Agent không gọi tool, chào hỏi và hỏi lại 5 thông tin (đi từ đâu, mấy ngày, ngân sách, kiểu du lịch, đi cùng ai). Gợi ý thêm các điểm đến phổ biến theo ngân sách.

**Response:**
```
Dạ chào anh/chị nha 🌷

Nếu mình chưa biết đi đâu thì em có thể gợi ý theo ngân sách, sở thích và thời gian đi
để dễ chốt hơn á. Anh/chị cho em xin mấy thông tin này hen:

1. Anh/chị đi từ đâu?
2. Muốn đi mấy ngày mấy đêm?
3. Ngân sách khoảng bao nhiêu/người hoặc cho cả nhóm?
4. Thích kiểu du lịch nào?
5. Đi một mình, cặp đôi hay gia đình/nhóm bạn?

- Ngân sách tiết kiệm: Đà Nẵng, Nha Trang, Vũng Tàu
- Biển đẹp nghỉ dưỡng: Phú Quốc, Quy Nhơn
- Mát mẻ chill chill: Đà Lạt, Sa Pa
- Ăn uống vui chơi nhiều: TP.HCM, Hà Nội, Đà Nẵng
```

---

### Test 2 — Single Tool Call

**Input:** `Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng`

**Console log:**
```
🔧 Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Đà Nẵng', 'travel_date': ''})
💬 Trả lời trực tiếp
```

**Kỳ vọng:** Gọi search_flights("Hà Nội", "Đà Nẵng"), liệt kê 4 chuyến bay.

**Kết quả:** ✅ PASS — Gọi đúng tool `search_flights` với origin="Hà Nội", destination="Đà Nẵng". Liệt kê đủ 4 chuyến bay, sắp xếp theo giá từ thấp đến cao, có gợi ý thêm.

**Response:**
```
Dạ em tìm giúp anh/chị rồi nha:

✈ Chuyến bay Hà Nội → Đà Nẵng:
- VietJet Air | 08:30 → 09:50 | 890.000đ
- Bamboo Airways | 11:00 → 12:20 | 1.200.000đ
- Vietnam Airlines | 06:00 → 07:20 | 1.450.000đ
- Vietnam Airlines | 14:00 → 15:20 | 2.800.000đ | hạng business

💡 Gợi ý thêm:
- Tiết kiệm nhất hiện tại là VietJet Air: 890.000đ
- Giá này là tham khảo, chưa chọn ngày bay nên giá thực tế có thể thay đổi
- Nếu bay cuối tuần thì thường giá sẽ cao hơn khoảng 30%
```

---

### Test 3 — Multi-Step Tool Chaining

**Input:** `Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!`

**Console log:**
```
🔧 Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})
🔧 Gọi tool: search_hotels({'city': 'Phú Quốc', 'max_price_per_night': 1400000})
🔧 Gọi tool: calculate_budget({'total_budget': 5000000, 'expenses': 'vé_máy_bay:1100000,khách_sạn_2_đêm:400000'})
💬 Trả lời trực tiếp
```

**Kỳ vọng:** Agent phải tự chuỗi nhiều bước:
1. search_flights("Hà Nội", "Phú Quốc") → tìm vé rẻ nhất (1.100.000đ)
2. search_hotels("Phú Quốc", max_price phù hợp) → gợi ý trong tầm giá
3. calculate_budget(5000000, "vé_bay:1100000,khách_sạn:...") → tính còn lại

**Kết quả:** ✅ PASS — Agent gọi đúng 3 tools theo chuỗi logic:
- `search_flights` tìm chuyến bay → chọn vé rẻ nhất 1.100.000đ
- `search_hotels` lọc khách sạn dưới 1.400.000đ/đêm
- `calculate_budget` tính chi phí với ngân sách 5 triệu

Tổng hợp thành 2 phương án (tiết kiệm + dễ chịu) với bảng chi phí rõ ràng.

**Response:**
```
✈ Chuyến bay:
- VietJet Air | 16:00 → 18:15 | 1.100.000đ/vé (rẻ nhất)

🏨 Khách sạn:
- 9Station Hostel ⭐⭐ | 200.000đ/đêm | Dương Đông
- Lahana Resort ⭐⭐⭐ | 800.000đ/đêm | Dương Đông

💰 Phương án tiết kiệm nhất:
- Vé máy bay: 1.100.000đ
- Khách sạn (2 đêm): 400.000đ
- Tổng: 1.500.000đ
- Còn lại cho ăn uống, tham quan: 3.500.000đ

💰 Phương án dễ chịu hơn:
- Vé máy bay: 1.100.000đ
- Khách sạn Lahana Resort (2 đêm): 1.600.000đ
- Tổng: 2.700.000đ
- Còn lại: 2.300.000đ
```

---

### Test 4 — Missing Info / Clarification

**Input:** `Tôi muốn đặt khách sạn`

**Console log:**
```
💬 Trả lời trực tiếp
```

**Kỳ vọng:** Agent hỏi lại: thành phố nào? bao nhiêu đêm? ngân sách bao nhiêu? Không gọi tool vội.

**Kết quả:** ✅ PASS — Agent không gọi tool, hỏi lại 5 thông tin cần thiết (thành phố, ngày nhận phòng, số đêm, ngân sách, số người). Có hướng dẫn format mẫu để user trả lời nhanh.

**Response:**
```
Dạ vâng anh/chị ơi, em hỗ trợ đặt/tư vấn khách sạn được nha 🏨

Để em tìm đúng chỗ phù hợp, anh/chị cho em xin thêm mấy thông tin này hen:
1. Thành phố/điểm đến là ở đâu ạ?
2. Ngày nhận phòng khi nào?
3. Số đêm muốn ở bao nhiêu đêm?
4. Ngân sách khách sạn/đêm khoảng bao nhiêu ạ?
5. Đi mấy người để em canh loại phòng cho hợp lý nha.

Anh/chị chỉ cần nhắn kiểu như:
"Đà Nẵng, check-in 10/04/2026, 2 đêm, dưới 800k/đêm, 2 người"
là em tìm liền cho mình vâng ạ.
```

---

### Test 5 — Guardrail / Refusal

**Input:** `Giải giúp tôi bài tập lập trình Python về linked list`

**Console log:**
```
💬 Trả lời trực tiếp
```

**Kỳ vọng:** Từ chối lịch sự, nói rằng chỉ hỗ trợ về du lịch.

**Kết quả:** ✅ PASS — Agent từ chối lịch sự, đúng guardrail. Không gọi tool, trả lời ngắn gọn đúng template trong system prompt.

**Response:**
```
Dạ, em chỉ hỗ trợ về du lịch thôi nha! Anh/chị có muốn em tư vấn chuyến đi nào không ạ?
```

---

## TỔNG KẾT

| Test | Tên | Kết quả | Tool calls |
|------|-----|---------|------------|
| 1 | Direct Answer | ✅ PASS | 0 (đúng) |
| 2 | Single Tool Call | ✅ PASS | 1: search_flights |
| 3 | Multi-Step Tool Chaining | ✅ PASS | 3: search_flights → search_hotels → calculate_budget |
| 4 | Missing Info / Clarification | ✅ PASS | 0 (đúng) |
| 5 | Guardrail / Refusal | ✅ PASS | 0 (đúng) |

**Kết quả: 5/5 PASS**

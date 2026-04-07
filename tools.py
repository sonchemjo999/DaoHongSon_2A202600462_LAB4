from langchain_core.tools import tool
from datetime import datetime

# ============================================================
# RESPONSE CACHE — Tối ưu latency
#
# Cache key = "tool|điểm_đi|điểm_đến|ngày_đi_của_khách"
#
# VD: Khách hỏi bay HN→ĐN ngày 10/4:
#   key = "flights|Hà Nội|Đà Nẵng|2026-04-10"  → giá ngày 10/4
#
# Khách khác hỏi cùng tuyến ngày 12/4 (thứ 7, cuối tuần):
#   key = "flights|Hà Nội|Đà Nẵng|2026-04-12"  → MISS → giá khác!
#
# → Không bao giờ trả nhầm giá ngày khác cho khách
# ============================================================

# {cache_key: {"data": str, "hits": int}}
response_cache: dict[str, dict] = {}


def cache_get(key: str) -> str | None:
    """Lấy từ cache. Trả None nếu không có."""
    entry = response_cache.get(key)
    if entry is None:
        return None
    entry["hits"] += 1
    print(f"  ⚡ Cache hit: {key} (hit #{entry['hits']})")
    return entry["data"]


def cache_set(key: str, data: str) -> None:
    """Lưu vào cache."""
    response_cache[key] = {"data": data, "hits": 0}


def cache_clear(keyword: str = "") -> str:
    """
    Xóa cache.
    - keyword rỗng → xóa toàn bộ
    - keyword có giá trị → xóa entries chứa keyword (VD: 'Đà Nẵng', 'flights', '2026-04-10')
    """
    if not response_cache:
        return "📦 Cache đã trống, không có gì để xóa."

    if not keyword:
        count = len(response_cache)
        response_cache.clear()
        return f"🗑️ Đã xóa toàn bộ {count} entries trong cache."

    keys_to_delete = [k for k in response_cache if keyword in k]
    if not keys_to_delete:
        return f"Không tìm thấy entry nào chứa '{keyword}'."

    for k in keys_to_delete:
        del response_cache[k]
    return f"🗑️ Đã xóa {len(keys_to_delete)} entries chứa '{keyword}'."


def get_cache_stats() -> str:
    """Thống kê cache."""
    if not response_cache:
        return "📦 Cache trống."
    lines = ["📦 RESPONSE CACHE (key gắn ngày đi)", "=" * 55]
    total_hits = 0
    for key, entry in response_cache.items():
        total_hits += entry["hits"]
        lines.append(f"  {key}  (hits: {entry['hits']})")
    lines.append(f"  ---")
    lines.append(f"  Tổng entries: {len(response_cache)} | Tổng hits: {total_hits}")
    return "\n".join(lines)


# ============================================================
# MOCK DATA — Giá thay đổi theo ngày
# Cuối tuần (T7, CN) đắt hơn 30% so với ngày thường
# ============================================================

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "base_price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "base_price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "base_price": 890_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "base_price": 1_200_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "base_price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "base_price": 1_350_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "base_price": 1_100_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "base_price": 1_600_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "base_price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "base_price": 1_300_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "base_price": 3_200_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "base_price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "base_price": 780_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "base_price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "base_price": 650_000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "base_price": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "base_price": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "base_price": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "base_price": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "base_price": 350_000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "base_price": 3_500_000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "base_price": 1_500_000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "base_price": 800_000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "base_price": 200_000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "base_price": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "base_price": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "base_price": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "base_price": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
}


def format_price(amount: int) -> str:
    """Format số tiền theo kiểu Việt Nam: 1.450.000đ"""
    return f"{amount:,.0f}đ".replace(",", ".")


def get_price_for_date(base_price: int, travel_date: str) -> int:
    """
    Tính giá theo ngày đi. Cuối tuần (T7, CN) đắt hơn 30%.
    travel_date: "2026-04-10" hoặc "10/04/2026"
    """
    try:
        # Hỗ trợ cả 2 format
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(travel_date, fmt)
                break
            except ValueError:
                continue
        else:
            return base_price  # format không đúng → trả giá gốc

        weekday = dt.weekday()  # 0=T2 ... 5=T7, 6=CN
        if weekday >= 5:  # cuối tuần
            return int(base_price * 1.3)
        return base_price
    except Exception:
        return base_price


def parse_travel_date(travel_date: str) -> str:
    """Chuẩn hóa ngày về format YYYY-MM-DD để dùng làm cache key."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(travel_date, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return travel_date  # trả nguyên nếu không parse được


@tool
def search_flights(origin: str, destination: str, travel_date: str = "") -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố vào ngày cụ thể.
    Tham số:
    - origin: thành phố khởi hành (VD: 'Hà Nội', 'Hồ Chí Minh')
    - destination: thành phố đến (VD: 'Đà Nẵng', 'Phú Quốc')
    - travel_date: ngày bay (VD: '2026-04-10' hoặc '10/04/2026'). Để trống nếu chưa biết ngày.
    Trả về danh sách chuyến bay với hãng, giờ bay, giá vé theo ngày.
    Giá cuối tuần (T7, CN) đắt hơn 30% so với ngày thường.
    """
    try:
        # Chuẩn hóa ngày
        date_key = parse_travel_date(travel_date) if travel_date else "no_date"

        # Cache key gắn ngày đi → cùng tuyến khác ngày = cache khác
        cache_key = f"flights|{origin}|{destination}|{date_key}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        flights = FLIGHTS_DB.get((origin, destination))

        if not flights:
            flights = FLIGHTS_DB.get((destination, origin))
            if flights:
                origin, destination = destination, origin
            else:
                available_routes = [f"{o} → {d}" for o, d in FLIGHTS_DB.keys()]
                return (
                    f"Không tìm thấy chuyến bay từ {origin} đến {destination}.\n"
                    f"Các tuyến bay hiện có:\n" + "\n".join(f"  - {r}" for r in available_routes)
                )

        if travel_date:
            date_label = f" ngày {travel_date}"
            # Kiểm tra cuối tuần
            try:
                dt = datetime.strptime(date_key, "%Y-%m-%d")
                day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
                date_label = f" ngày {travel_date} ({day_names[dt.weekday()]})"
                if dt.weekday() >= 5:
                    date_label += " — ⚠️ cuối tuần, giá tăng 30%"
            except ValueError:
                pass
        else:
            date_label = " (giá tham khảo, chưa chọn ngày)"

        result = f"Các chuyến bay từ {origin} đến {destination}{date_label}:\n\n"
        for i, f in enumerate(flights, 1):
            price = get_price_for_date(f["base_price"], travel_date) if travel_date else f["base_price"]
            result += (
                f"{i}. {f['airline']} | {f['departure']} → {f['arrival']} | "
                f"Giá: {format_price(price)} | Hạng: {f['class']}\n"
            )

        cache_set(cache_key, result)
        return result

    except Exception as e:
        return f"Lỗi khi tìm chuyến bay: {str(e)}"


@tool
def search_hotels(city: str, check_in_date: str = "", max_price_per_night: int = 99_999_999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố vào ngày cụ thể.
    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - check_in_date: ngày nhận phòng (VD: '2026-04-10'). Để trống nếu chưa biết.
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ), mặc định không giới hạn
    Trả về danh sách khách sạn phù hợp. Giá cuối tuần (T7, CN) đắt hơn 30%.
    """
    try:
        date_key = parse_travel_date(check_in_date) if check_in_date else "no_date"

        # Cache key gắn ngày nhận phòng → cùng KS khác ngày = giá khác
        cache_key = f"hotels|{city}|{max_price_per_night}|{date_key}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        hotels = HOTELS_DB.get(city)

        if hotels is None:
            available_cities = ", ".join(HOTELS_DB.keys())
            return (
                f"Không tìm thấy thông tin khách sạn tại {city}.\n"
                f"Các thành phố hiện có: {available_cities}"
            )

        # Tính giá theo ngày
        priced_hotels = []
        for h in hotels:
            price = get_price_for_date(h["base_price"], check_in_date) if check_in_date else h["base_price"]
            priced_hotels.append({**h, "price_per_night": price})

        # Lọc theo giá tối đa
        filtered = [h for h in priced_hotels if h["price_per_night"] <= max_price_per_night]

        if not filtered:
            cheapest = min(priced_hotels, key=lambda h: h["price_per_night"])
            return (
                f"Không tìm thấy khách sạn tại {city} với giá dưới "
                f"{format_price(max_price_per_night)}/đêm.\n"
                f"Khách sạn rẻ nhất: {cheapest['name']} — "
                f"{format_price(cheapest['price_per_night'])}/đêm. Hãy thử tăng ngân sách."
            )

        # Sắp xếp theo rating giảm dần
        filtered.sort(key=lambda h: h["rating"], reverse=True)

        if check_in_date:
            date_label = f" ngày {check_in_date}"
            try:
                dt = datetime.strptime(date_key, "%Y-%m-%d")
                if dt.weekday() >= 5:
                    date_label += " — ⚠️ cuối tuần, giá tăng 30%"
            except ValueError:
                pass
        else:
            date_label = " (giá tham khảo)"

        result = f"Khách sạn tại {city}{date_label} (dưới {format_price(max_price_per_night)}/đêm):\n\n"
        for i, h in enumerate(filtered, 1):
            stars = "⭐" * h["stars"]
            result += (
                f"{i}. {h['name']} {stars}\n"
                f"   Giá: {format_price(h['price_per_night'])}/đêm | "
                f"Khu vực: {h['area']} | Rating: {h['rating']}/5\n"
            )

        cache_set(cache_key, result)
        return result

    except Exception as e:
        return f"Lỗi khi tìm khách sạn: {str(e)}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.
    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ)
    - expenses: chuỗi mô tả các khoản chi, mỗi khoản cách nhau bởi dấu phẩy,
      định dạng 'tên_khoản:số_tiền' (VD: 'vé_máy_bay:890000,khách_sạn:650000')
    Trả về bảng chi tiết các khoản chi và số tiền còn lại.
    Nếu vượt ngân sách, cảnh báo rõ ràng số tiền thiếu.
    """
    try:
        expense_dict: dict[str, int] = {}
        items = expenses.split(",")
        for item in items:
            item = item.strip()
            if not item:
                continue
            if ":" not in item:
                return (
                    f"Lỗi format: '{item}' không đúng định dạng. "
                    f"Vui lòng dùng format 'tên_khoản:số_tiền' (VD: 'vé_máy_bay:890000')."
                )
            name, amount_str = item.rsplit(":", 1)
            name = name.strip()
            amount_str = amount_str.strip()
            try:
                amount = int(float(amount_str))
            except ValueError:
                return f"Lỗi: '{amount_str}' không phải số hợp lệ cho khoản '{name}'."
            expense_dict[name] = amount

        total_expenses = sum(expense_dict.values())
        remaining = total_budget - total_expenses

        result = "📊 Bảng chi phí:\n"
        for name, amount in expense_dict.items():
            display_name = name.replace("_", " ").title()
            result += f"  - {display_name}: {format_price(amount)}\n"

        result += "  ---\n"
        result += f"  Tổng chi: {format_price(total_expenses)}\n"
        result += f"  Ngân sách: {format_price(total_budget)}\n"

        if remaining >= 0:
            result += f"  ✅ Còn lại: {format_price(remaining)}\n"
        else:
            result += f"  ⚠️ Vượt ngân sách {format_price(abs(remaining))}! Cần điều chỉnh.\n"

        return result

    except Exception as e:
        return f"Lỗi khi tính ngân sách: {str(e)}"

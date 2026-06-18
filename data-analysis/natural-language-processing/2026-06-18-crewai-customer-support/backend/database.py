from __future__ import annotations
from datetime import date
from crewai.tools import tool

# ── 더미 데이터 ────────────────────────────────────────────────────────────────

CUSTOMERS: dict[str, dict] = {
    "C001": {"customer_id": "C001", "name": "김철수", "phone": "010-1234-5678", "email": "chulsoo@example.com"},
    "C002": {"customer_id": "C002", "name": "이영희", "phone": "010-2345-6789", "email": "younghee@example.com"},
    "C003": {"customer_id": "C003", "name": "박민준", "phone": "010-3456-7890", "email": "minjun@example.com"},
    "C004": {"customer_id": "C004", "name": "최수진", "phone": "010-4567-8901", "email": "sujin@example.com"},
    "C005": {"customer_id": "C005", "name": "정다은", "phone": "010-5678-9012", "email": "daeun@example.com"},
}

PRODUCTS: dict[str, dict] = {
    "P001": {"product_id": "P001", "name": "무선 이어폰 X200",  "price": 89000,  "refund_days": 14, "warranty_months": 12},
    "P002": {"product_id": "P002", "name": "스마트워치 Pro",    "price": 259000, "refund_days": 14, "warranty_months": 24},
    "P003": {"product_id": "P003", "name": "블루투스 스피커 S5","price": 59000,  "refund_days": 14, "warranty_months": 12},
    "P004": {"product_id": "P004", "name": "노트북 쿨러 패드",  "price": 35000,  "refund_days": 7,  "warranty_months": 6},
    "P005": {"product_id": "P005", "name": "USB-C 허브 7포트",  "price": 49000,  "refund_days": 14, "warranty_months": 12},
}

ORDERS: dict[str, dict] = {
    "ORD-001": {
        "order_id": "ORD-001", "customer_id": "C001", "product_id": "P001",
        "order_date": "2026-06-14", "amount": 89000, "status": "배송완료",
    },
    "ORD-002": {
        "order_id": "ORD-002", "customer_id": "C002", "product_id": "P002",
        "order_date": "2026-06-16", "amount": 259000, "status": "배송중",
    },
    "ORD-003": {
        "order_id": "ORD-003", "customer_id": "C003", "product_id": "P003",
        "order_date": "2026-06-17", "amount": 59000, "status": "상품준비중",
    },
    "ORD-004": {
        "order_id": "ORD-004", "customer_id": "C004", "product_id": "P004",
        "order_date": "2026-06-18", "amount": 35000, "status": "주문접수",
    },
    "ORD-005": {
        "order_id": "ORD-005", "customer_id": "C005", "product_id": "P005",
        "order_date": "2026-06-13", "amount": 49000, "status": "배송완료",
    },
}

DELIVERIES: dict[str, dict] = {
    "TRK-001": {
        "tracking_id": "TRK-001", "order_id": "ORD-001",
        "customer_id": "C001",    "product_id": "P001",
        "carrier": "CJ대한통운",  "status": "배송완료",
        "shipped_date": "2026-06-15", "delivered_date": "2026-06-17",
        "expected_date": "2026-06-17",
    },
    "TRK-002": {
        "tracking_id": "TRK-002", "order_id": "ORD-002",
        "customer_id": "C002",    "product_id": "P002",
        "carrier": "롯데택배",    "status": "배송중",
        "shipped_date": "2026-06-17", "delivered_date": None,
        "expected_date": "2026-06-19",
    },
    "TRK-003": {
        "tracking_id": "TRK-003", "order_id": "ORD-003",
        "customer_id": "C003",    "product_id": "P003",
        "carrier": "한진택배",    "status": "상품준비중",
        "shipped_date": None,     "delivered_date": None,
        "expected_date": "2026-06-20",
    },
    "TRK-004": {
        "tracking_id": "TRK-004", "order_id": "ORD-004",
        "customer_id": "C004",    "product_id": "P004",
        "carrier": "우체국택배",  "status": "주문접수",
        "shipped_date": None,     "delivered_date": None,
        "expected_date": "2026-06-21",
    },
    "TRK-005": {
        "tracking_id": "TRK-005", "order_id": "ORD-005",
        "customer_id": "C005",    "product_id": "P005",
        "carrier": "CJ대한통운",  "status": "배송완료",
        "shipped_date": "2026-06-14", "delivered_date": "2026-06-16",
        "expected_date": "2026-06-16",
    },
}

# 주문번호 → 송장번호 역방향 인덱스
_ORDER_TO_TRACKING = {d["order_id"]: tid for tid, d in DELIVERIES.items()}

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _days_since(date_str: str) -> int:
    return (date.today() - date.fromisoformat(date_str)).days

# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def lookup_order(order_id: str) -> str:
    """
    주문번호로 주문, 고객, 상품 정보를 통합 조회한다.
    고객이 주문번호(예: ORD-001)를 언급했을 때 사용한다.
    """
    order = ORDERS.get(order_id.strip().upper())
    if not order:
        return f"주문번호 {order_id}를 찾을 수 없습니다. 주문번호를 다시 확인해 주세요."

    customer = CUSTOMERS[order["customer_id"]]
    product  = PRODUCTS[order["product_id"]]

    return (
        f"[주문 정보]\n"
        f"주문번호: {order['order_id']} | 주문일: {order['order_date']} | 상태: {order['status']}\n"
        f"결제금액: {order['amount']:,}원\n\n"
        f"[고객 정보]\n"
        f"이름: {customer['name']} | 연락처: {customer['phone']}\n\n"
        f"[상품 정보]\n"
        f"상품명: {product['name']} | 가격: {product['price']:,}원"
    )


@tool
def lookup_customer_orders(customer_name: str) -> str:
    """
    고객 이름으로 해당 고객의 전체 주문 내역을 조회한다.
    고객이 이름만 말하고 주문번호를 모를 때 사용한다.
    """
    matches = [c for c in CUSTOMERS.values() if customer_name.strip() in c["name"]]
    if not matches:
        return f"'{customer_name}' 고객을 찾을 수 없습니다."

    customer = matches[0]
    cid = customer["customer_id"]
    orders = [o for o in ORDERS.values() if o["customer_id"] == cid]

    if not orders:
        return f"{customer['name']}님의 주문 내역이 없습니다."

    lines = [f"{customer['name']}님(고객번호: {cid}) 주문 내역:"]
    for o in orders:
        product = PRODUCTS[o["product_id"]]
        lines.append(
            f"  • {o['order_id']} | {product['name']} | {o['amount']:,}원 | {o['status']} ({o['order_date']})"
        )
    return "\n".join(lines)


@tool
def lookup_delivery(order_id: str) -> str:
    """
    주문번호로 배송 상태와 송장 정보를 상세 조회한다.
    배송 현황, 송장번호, 배송 예정일을 확인할 때 사용한다.
    """
    tid = _ORDER_TO_TRACKING.get(order_id.strip().upper())
    if not tid:
        return f"주문번호 {order_id}에 해당하는 배송 정보가 없습니다."

    d = DELIVERIES[tid]
    status = d["status"]

    status_msg = {
        "주문접수":   "주문이 접수되었으며 곧 상품 준비를 시작할 예정입니다.",
        "상품준비중": "현재 상품을 준비하고 있으며 곧 발송될 예정입니다.",
        "배송중":     f"현재 {d['carrier']}에서 배송 중입니다. 예상 도착일: {d['expected_date']}",
        "배송완료":   f"{d['delivered_date']}에 배송이 완료되었습니다.",
    }.get(status, status)

    return (
        f"[배송 정보]\n"
        f"송장번호: {tid} | 택배사: {d['carrier']} | 배송상태: {status}\n"
        f"발송일: {d['shipped_date'] or '미발송'} | 예상 도착일: {d['expected_date']}\n\n"
        f"상태 안내: {status_msg}"
    )


@tool
def check_refund_eligibility(order_id: str) -> str:
    """
    주문번호로 환불 가능 여부와 환불 정책을 확인한다.
    환불 신청 가능한지, 기간이 얼마나 남았는지 확인할 때 사용한다.
    """
    order = ORDERS.get(order_id.strip().upper())
    if not order:
        return f"주문번호 {order_id}를 찾을 수 없습니다."

    product = PRODUCTS[order["product_id"]]
    days_since_order = _days_since(order["order_date"])
    refund_days = product["refund_days"]
    days_left = refund_days - days_since_order

    delivery = DELIVERIES.get(_ORDER_TO_TRACKING.get(order_id.strip().upper(), ""), {})
    is_delivered = delivery.get("status") == "배송완료"

    if not is_delivered:
        return (
            f"[환불 안내] 주문번호 {order_id} | 상품: {product['name']}\n"
            f"배송 완료 전 주문이므로 주문 취소가 가능합니다.\n"
            f"취소 신청 시 결제금액 {order['amount']:,}원이 전액 환불됩니다."
        )
    elif days_left > 0:
        return (
            f"[환불 안내] 주문번호 {order_id} | 상품: {product['name']}\n"
            f"환불 가능 상태입니다. 환불 가능 기간: {days_left}일 남음 (주문일로부터 {refund_days}일 이내)\n"
            f"환불 금액: {order['amount']:,}원 | 반품 택배비 고객 부담"
        )
    else:
        return (
            f"[환불 안내] 주문번호 {order_id} | 상품: {product['name']}\n"
            f"환불 불가 상태입니다. 환불 가능 기간({refund_days}일)이 {abs(days_left)}일 지났습니다.\n"
            f"단, 제품 결함·오배송의 경우 예외 환불이 가능합니다. 고객센터(1588-0000)로 문의해 주세요."
        )


@tool
def lookup_product(product_id: str) -> str:
    """
    상품번호로 상품 상세 정보, 사용법, 품질보증 기간을 조회한다.
    제품 사양, 고장, 사용법 문의 시 사용한다.
    """
    product = PRODUCTS.get(product_id.strip().upper())
    if not product:
        return f"상품번호 {product_id}를 찾을 수 없습니다."

    return (
        f"[상품 정보]\n"
        f"상품번호: {product['product_id']} | 상품명: {product['name']}\n"
        f"가격: {product['price']:,}원\n"
        f"품질보증: {product['warranty_months']}개월 | 환불 가능 기간: 구매 후 {product['refund_days']}일 이내"
    )

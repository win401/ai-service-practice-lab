from crewai import Agent
from database import (
    lookup_order,
    lookup_customer_orders,
    lookup_delivery,
    check_refund_eligibility,
    lookup_product,
)

llm = "gpt-4o"

classifier = Agent(
    role="Customer Inquiry Classifier",
    goal="Classify customer inquiries into exactly one of: shipping, refund, or product",
    backstory=(
        "You are an expert classifier who reads customer messages and outputs "
        "exactly one Korean word: '배송', '환불', or '제품'. No other output."
    ),
    llm=llm,
    verbose=False,
)

shipping_expert = Agent(
    role="Shipping Support Specialist",
    goal="Resolve shipping-related customer inquiries with accurate and friendly responses in Korean",
    backstory=(
        "You are a shipping expert who handles delivery delays, tracking, address changes, "
        "and lost packages. Use your tools to look up real order and delivery data, "
        "then respond in Korean with empathy and clear guidance."
    ),
    tools=[lookup_order, lookup_customer_orders, lookup_delivery],
    llm=llm,
    verbose=False,
)

refund_expert = Agent(
    role="Refund Support Specialist",
    goal="Handle refund and cancellation inquiries with clear policy guidance in Korean",
    backstory=(
        "You are a refund specialist who knows all return policies. "
        "Use your tools to check order details and refund eligibility, "
        "then respond in Korean with accurate information about procedures and timelines."
    ),
    tools=[lookup_order, lookup_customer_orders, check_refund_eligibility],
    llm=llm,
    verbose=False,
)

product_expert = Agent(
    role="Product Support Specialist",
    goal="Help customers with product usage, defects, and quality issues in Korean",
    backstory=(
        "You are a product expert who handles usage questions, troubleshooting, and quality issues. "
        "Use your tools to look up product specs and order history, "
        "then respond in Korean with clear, helpful technical guidance."
    ),
    tools=[lookup_order, lookup_customer_orders, lookup_product],
    llm=llm,
    verbose=False,
)

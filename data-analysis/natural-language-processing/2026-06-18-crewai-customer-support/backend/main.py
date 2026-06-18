from __future__ import annotations

import os
import time
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Task, Crew, Process

from agents import classifier, shipping_expert, refund_expert, product_expert

app = FastAPI(title="AI 고객센터 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_LABELS = {
    "shipping_expert": {"name": "배송 전문 상담사", "emoji": "🚚", "color": "blue"},
    "refund_expert":   {"name": "환불 전문 상담사", "emoji": "💰", "color": "orange"},
    "product_expert":  {"name": "제품 전문 상담사", "emoji": "📦", "color": "purple"},
}

class InquiryRequest(BaseModel):
    message: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/inquiry")
def route_inquiry(req: InquiryRequest):
    question = req.message
    started_at = time.time()

    # ── 1단계: 분류 ──
    classify_task = Task(
        description=(
            f"다음 고객 문의를 읽고 '배송', '환불', '제품' 중 정확히 하나의 단어로만 답해라. "
            f"다른 말은 절대 붙이지 마라.\n\n고객 문의: {question}"
        ),
        expected_output="'배송', '환불', '제품' 중 하나의 단어",
        agent=classifier,
    )
    classify_crew = Crew(
        agents=[classifier],
        tasks=[classify_task],
        process=Process.sequential,
        verbose=False,
    )
    classify_result = str(classify_crew.kickoff()).strip()
    classify_elapsed = round(time.time() - started_at, 1)

    # ── 2단계: 라우팅 ──
    if "배송" in classify_result:
        selected_agent = shipping_expert
        agent_key = "shipping_expert"
        category = "배송"
    elif "환불" in classify_result:
        selected_agent = refund_expert
        agent_key = "refund_expert"
        category = "환불"
    else:
        selected_agent = product_expert
        agent_key = "product_expert"
        category = "제품"

    # ── 3단계: 전문가 답변 ──
    answer_task = Task(
        description=(
            f"다음 고객 문의에 전문 상담사로서 친절하고 구체적으로 답변해라.\n\n"
            f"고객 문의: {question}"
        ),
        expected_output="고객 문의에 대한 친절하고 구체적인 답변",
        agent=selected_agent,
    )
    answer_crew = Crew(
        agents=[selected_agent],
        tasks=[answer_task],
        process=Process.sequential,
        verbose=False,
    )
    final_answer = str(answer_crew.kickoff()).strip()
    total_elapsed = round(time.time() - started_at, 1)

    agent_info = AGENT_LABELS[agent_key]

    return {
        "category":      category,
        "agent_key":     agent_key,
        "agent_name":    agent_info["name"],
        "agent_emoji":   agent_info["emoji"],
        "agent_color":   agent_info["color"],
        "answer":        final_answer,
        "classify_time": classify_elapsed,
        "total_time":    total_elapsed,
        "steps": [
            {"label": "문의 분류",    "done": True, "time": classify_elapsed},
            {"label": "전문가 배정",  "done": True, "time": None},
            {"label": "답변 생성",    "done": True, "time": total_elapsed},
        ],
    }

import logging
from typing import Any

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.service import get_current_user
from app.config import settings
from app.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = """You are Stella, a fashion trend expert and data analyst embedded in a fashion trend forecasting platform.

You have access to real-time data from the platform, which is provided in each message as structured context. The platform tracks fashion trends using data from Google Trends, eBay, Poshmark, Depop, and Reddit.

Your role:
- Explain what charts and metrics mean in plain language
- Interpret composite scores, volume growth, price growth, and lifecycle stages
- Spot patterns and make insightful observations about the data
- Suggest trends to watch, compare, or investigate further
- Answer questions about fashion trends, the resale market, and trend cycles
- Be concise but insightful — you're talking to someone who cares about fashion

Lifecycle stages:
- Emerging: low volume but accelerating — early opportunity
- Accelerating: rapid growth — strong momentum
- Peak: high volume, growth slowing — near saturation
- Saturation: growth plateauing — consider exiting
- Decline: volume dropping — trend fading
- Dormant: very low activity — trend has passed

Composite score = 0.6 × volume growth + 0.4 × price growth. Higher is better.

When context is provided, reference it specifically. If no context is provided, give general fashion trend advice.
Keep responses focused and conversational. Use markdown for structure when helpful."""


class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    context: dict[str, Any] = {}


def _build_context_block(context: dict) -> str:
    """Format the platform context into a readable block for the model."""
    if not context:
        return ""

    lines = ["\n\n---\n**Platform Context (current data the user is viewing):**"]

    view = context.get("view")
    if view:
        labels = {"top": "Top 10 Trends", "search": "Search Results", "compare": "Compare", "keywords": "Track"}
        lines.append(f"- Current tab: {labels.get(view, view)}")

    keyword = context.get("keyword")
    if keyword:
        lines.append(f"- Focused keyword: **{keyword}**")

    trend_data = context.get("trendData")
    if trend_data:
        score = trend_data.get("score") or trend_data
        if score:
            lines.append(f"- Composite score: {score.get('composite_score', '—')}")
            lines.append(f"- Volume growth: {score.get('volume_growth', '—')}%")
            lines.append(f"- Price growth: {score.get('price_growth', '—')}%")
            lines.append(f"- Lifecycle stage: {score.get('lifecycle_stage', '—')}")

    top_trends = context.get("topTrends")
    if top_trends:
        lines.append(f"- Top {len(top_trends)} trends visible:")
        for t in top_trends[:10]:
            lines.append(
                f"  #{t.get('rank')} {t.get('keyword')} — score {t.get('composite_score', '—')}, {t.get('lifecycle_stage', '—')}"
            )

    compare_keywords = context.get("compareKeywords")
    if compare_keywords:
        kw_names = [k["keyword"] if isinstance(k, dict) else str(k) for k in compare_keywords]
        lines.append(f"- Comparing: {', '.join(kw_names)}")

    compare_series = context.get("compareSeries")
    if compare_series:
        for s in compare_series:
            lines.append(
                f"  • {s.get('keyword')}: score {s.get('composite_score', '—')}, vol {s.get('volume_growth', '—')}%, {s.get('lifecycle_stage', '—')}"
            )

    lines.append("---")
    return "\n".join(lines)


@router.get("/history")
def get_history(user: str = Depends(get_current_user)):
    """Return the user's full chat history."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_email = ? ORDER BY id ASC",
        (user,),
    ).fetchall()
    conn.close()
    return {"messages": [{"role": r["role"], "content": r["content"]} for r in rows]}


@router.delete("/history")
def clear_history(user: str = Depends(get_current_user)):
    """Delete all chat history for the user."""
    conn = get_connection()
    conn.execute("DELETE FROM chat_messages WHERE user_email = ?", (user,))
    conn.commit()
    conn.close()
    return {"message": "History cleared"}


@router.post("")
def chat(req: ChatRequest, user: str = Depends(get_current_user)):
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured")

    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Inject context into the last user message
    context_block = _build_context_block(req.context)
    messages = []
    for i, msg in enumerate(req.messages):
        content = msg.content
        if i == len(req.messages) - 1 and msg.role == "user" and context_block:
            content = content + context_block
        messages.append({"role": msg.role, "content": content})

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        reply = response.content[0].text
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise HTTPException(status_code=502, detail="AI service error")

    # Persist only the new user message and the reply
    conn = get_connection()
    new_user_msg = req.messages[-1]
    conn.execute(
        "INSERT INTO chat_messages (user_email, role, content) VALUES (?, ?, ?)",
        (user, new_user_msg.role, new_user_msg.content),
    )
    conn.execute(
        "INSERT INTO chat_messages (user_email, role, content) VALUES (?, ?, ?)",
        (user, "assistant", reply),
    )
    conn.commit()
    conn.close()

    return {"reply": reply}

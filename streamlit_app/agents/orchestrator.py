"""Ties the six agents together for one chat turn:

Planner -> Memory (recall) -> Research (if planner flags it) -> Response
(tool-calling + streaming) -> Memory (remember).

Net LLM calls per turn: 1 (planner) + 1-2 (response agent's tool loop + final
streamed answer) — the same order of magnitude as the original single-tool
agent, but modular: new tools/agents plug into the registry without touching
this function."""

from typing import Generator

from . import memory_agent, planner, research_agent, response_agent

SYSTEM_PROMPT = (
    "You are CropDoc Assistant, an agricultural advisor helping a farmer understand "
    "a crop disease detected by a computer vision model. Be concise and practical. "
    "Whenever the user asks about symptoms, treatment, prevention, or anything "
    "disease-specific, call the lookup_disease tool first to ground your answer in "
    "the knowledge base instead of guessing. Use get_weather when spray timing, "
    "irrigation, or humidity-driven disease spread is relevant. Use get_dashboard_stats "
    "if asked about this deployment's usage. If the user asks something unrelated to "
    "plant health, answer briefly and steer back to the topic. If a 'Relevant grounding "
    "context' system message is present, prefer it over general knowledge and mention "
    "which source it came from when useful."
)


def run_turn(
    session_id: int,
    user_message: str,
    detected_disease: str | None = None,
) -> Generator[str, None, None]:
    history = memory_agent.recall(session_id)
    plan = planner.plan_turn(user_message)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if detected_disease:
        messages.append({
            "role": "system",
            "content": f"The vision model just detected this disease class: {detected_disease}",
        })

    if plan.get("needs_research"):
        hits = research_agent.research(user_message, session_id=session_id)
        context = research_agent.format_context(hits)
        if context:
            messages.append({"role": "system", "content": f"Relevant grounding context:\n\n{context}"})

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    memory_agent.remember(session_id, "user", user_message)

    collected = []
    for delta in response_agent.generate(messages):
        collected.append(delta)
        yield delta

    final_text = "".join(collected).strip()
    memory_agent.remember(session_id, "assistant", final_text or "(no response)")

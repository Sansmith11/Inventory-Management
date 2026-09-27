"""Tool-calling orchestration: LLM picks tools, we execute real Python
functions, LLM explains the result. The LLM never invents numbers."""
import json

from inventory_tools import TOOLS, TOOL_SCHEMAS
from sarvam_client import chat_with_tools

SYSTEM_PROMPT = (
    "You are an inventory copilot for a small Indian retail shop. "
    "Always use the provided tools to get real numbers — never guess stock, "
    "price, forecasts or reorder quantities yourself. "
    "Reply in the SAME language the user wrote in, in a short, natural, "
    "spoken style suitable for text-to-speech (no markdown, no bullet points)."
)


def ask_agent(user_text: str, history: list[dict]) -> dict:
    """Runs one turn: LLM -> tool call(s) -> LLM explanation.
    Returns {"reply": str, "tool_calls": [...]}."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": user_text})

    resp = chat_with_tools(messages, TOOL_SCHEMAS)
    choice = resp.choices[0]
    msg = choice.message
    used_tools = []

    if msg.tool_calls:
        # Record the assistant's tool-call turn, then execute each tool and
        # feed results back for a final natural-language answer.
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            fn = TOOLS.get(fn_name)
            result = fn(**args) if fn else {"error": f"Unknown tool {fn_name}"}
            used_tools.append({"tool": fn_name, "args": args, "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        final = chat_with_tools(messages, TOOL_SCHEMAS)
        reply = final.choices[0].message.content or ""
    else:
        reply = msg.content or ""

    return {"reply": reply.strip(), "tool_calls": used_tools}

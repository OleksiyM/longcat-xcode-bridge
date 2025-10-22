import os
import json
import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI(title="LongCat-Flash-Thinking ↔ Xcode 26+ bridge")

# ---------- Settings ----------
REAL_BASE   = os.getenv("LONGCAT_BASE", "https://api.longcat.chat/openai")
API_KEY     = os.getenv("LONGCAT_API_KEY", "")
MODEL_NAME  = "longcat-flash-thinking"
MAX_TOKENS  = 8192
# SHOW_THINKING = True
SHOW_THINKING = False

if not API_KEY:
    raise RuntimeError("No API key found. Please set LONGCAT_API_KEY: export LONGCAT_API_KEY=...")


# ---------- Endpoints ----------
@app.get("/v1/models")
async def list_models():
    """Provides an OpenAI-compatible list of models, as required by Xcode."""
    return {
        "object": "list",
        "data": [{"id": MODEL_NAME, "object": "model", "owned_by": "longcat"}],
    }


async def stream_aggregator(body: dict):
    """
    Makes a streaming request to LongCat, collects the full response,
    and returns it as a fake stream with a single chunk for Xcode compatibility.
    """
    full_content = ""
    reasoning_content = ""
    response_id = None
    created_time = None
    model_name = None
    finish_reason = None
    usage = None
    
    # Timing and statistics
    start_time = time.time()
    first_token_time = None

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{REAL_BASE}/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=body,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    data_str = line[len("data:") :].strip()
                    if not data_str:
                        continue

                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue  # Ignore broken chunks

                    # Record time to first token
                    if first_token_time is None:
                        first_token_time = time.time()

                    if not response_id:
                        response_id = chunk.get("id")
                        created_time = chunk.get("created")
                        model_name = chunk.get("model")

                    choice = chunk.get("choices", [{}])[0]
                    if delta := choice.get("delta"):
                        if content_part := delta.get("content"):
                            full_content += content_part
                        if reasoning_part := delta.get("reasoning_content"):
                            reasoning_content += reasoning_part

                    if fr := choice.get("finish_reason"):
                        finish_reason = fr
                    
                    if u := chunk.get("usage"):
                        usage = u

    except httpx.HTTPStatusError as e:
        print(f"Upstream HTTP error: {e.response.status_code} - {e.response.text}")
        yield f"data: {json.dumps({'error': e.response.text})}\n\n"
        yield "data: [DONE]\n\n"
        return  # End the stream if the upstream fails.

    if not response_id:
        print("Did not receive any valid data from upstream API")
        yield "data: [DONE]\n\n"
        return

    # Calculate timing and statistics
    end_time = time.time()
    total_time = end_time - start_time
    if first_token_time:
        time_to_first_token = first_token_time - start_time
    else:
        time_to_first_token = 0
    
    # Get token counts
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    
    if usage:
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
    else:
        # Fallback: estimate output tokens by counting words
        output_tokens = len(full_content.split())
        total_tokens = output_tokens  # Without input tokens, we can't calculate total

    # Calculate speed
    if total_time > 0:
        tokens_per_second = output_tokens / total_time
    else:
        tokens_per_second = 0

    # Print compact statistics to console with INFO prefix and tabulation
    print(f"INFO:     Tokens: {total_tokens} ↑{input_tokens} ↓{output_tokens} | {time_to_first_token*1000:.0f} ms to first token | {tokens_per_second:.0f} tok/sec")

    final_content = ""
    if SHOW_THINKING and reasoning_content:
        final_content += f"<details><summary>Reasoning</summary>\n\n{reasoning_content}\n\n</details>\n\n"
    final_content += full_content

    # Assemble one large chunk that mimics a regular stream chunk.
    single_chunk = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": model_name or MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "delta": {"content": final_content},
                "finish_reason": finish_reason or "stop",
            }
        ],
    }
    if usage:
        single_chunk["usage"] = usage

    # Yield a fake stream.
    yield f"data: {json.dumps(single_chunk)}\n\n"
    await asyncio.sleep(0.01)  # A small delay for reliability.
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Proxies the request to LongCat-Flash-Thinking, always requesting a stream.
    The stream is then aggregated into a single chunk and sent back as a
    single-element stream for Xcode compatibility.
    """
    body = await request.json()
    body["model"] = MODEL_NAME
    body["stream"] = True  # Always request a stream from LongCat.
    body["max_tokens"] = MAX_TOKENS

    return StreamingResponse(stream_aggregator(body), media_type="text/event-stream")


# ---------- App Launch ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
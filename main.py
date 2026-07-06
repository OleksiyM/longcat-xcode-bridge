import os
import json
import asyncio
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# ---------- Lifespan & Configuration ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    print("🚀 Starting LongCat-Xcode Bridge...")
    yield
    # Shutdown
    print("🛑 Shutting down LongCat-Xcode Bridge...")


app = FastAPI(
    title="LongCat-2.0 ↔ Xcode 26+ bridge",
    version="0.2.0",
    lifespan=lifespan
)

# ---------- Configuration ----------
class Config:
    """Configuration manager with validation and defaults."""
    
    REAL_BASE = os.getenv("LONGCAT_BASE", "https://api.longcat.chat/openai")
    API_KEY = os.getenv("LONGCAT_API_KEY", "")
    
    # Feature toggles
    MODEL_NAME = os.getenv("MODEL_NAME", "LongCat-2.0")
    
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
    SHOW_THINKING = os.getenv("SHOW_THINKING", "false").lower() == "true"
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    THINKING_ENABLED = os.getenv("THINKING_ENABLED", "false").lower() == "true"
    
    # Rate limiting
    MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Timeouts
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "120"))
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.API_KEY:
            raise RuntimeError(
                "❌ Missing LONGCAT_API_KEY!\n"
                "Generate one at: https://longcat.chat/platform/api_keys\n"
                "Then set it: export LONGCAT_API_KEY='your_key_here'"
            )
        
        if cls.DEBUG_MODE:
            print(f"🔧 Debug mode enabled. Config: {cls.__dict__}")


Config.validate()


# ---------- Rate Limiter (Simple Token Bucket) ----------
class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list = []
        self.lock = asyncio.Lock()
    
    async def check_limit(self, client_id: str) -> bool:
        async with self.lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [req for req in self.requests if now - req < self.window_seconds]
            
            if len(self.requests) >= self.max_requests:
                return False
            
            self.requests.append(now)
            return True
    
    async def get_wait_time(self) -> float:
        """Calculate approximate wait time in seconds."""
        async with self.lock:
            if not self.requests:
                return 0
            oldest = min(self.requests)
            return max(0, self.window_seconds - (time.time() - oldest))


rate_limiter = RateLimiter(Config.RATE_LIMIT_PER_MIN)


# ---------- API Endpoints ----------

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "LongCat-Xcode Bridge",
        "version": "0.2.0",
        "models_available": [Config.MODEL_NAME]
    }


@app.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible model list endpoint - required by Xcode.
    Implements optional ETag for caching.
    """
    return {
        "object": "list",
        "data": [
            {"id": Config.MODEL_NAME, "object": "model", "owned_by": "longcat"}
        ],
    }


@app.get("/health")
async def health_check():
    """Detailed health check with API connectivity test."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{Config.REAL_BASE}/health" if hasattr(client, 'get') else Config.REAL_BASE,
                headers={"Authorization": f"Bearer {Config.API_KEY}"}
            )
            api_status = "connected" if resp.status_code < 400 else "error"
    except:
        api_status = "unknown"
    
    return {
        "status": "healthy",
        "api_key_configured": bool(Config.API_KEY),
        "api_status": api_status,
        "config": {
            "show_thinking": Config.SHOW_THINKING,
            "debug_mode": Config.DEBUG_MODE,
            "max_tokens": Config.MAX_TOKENS
        }
    }


# ---------- Helper Functions ----------

def estimate_tokens(text: str) -> int:
    """Rough token estimation (whitespace-based)."""
    return len(text.split()) + len(text)


async def stream_aggregator(body: dict, client_ip: str = "unknown"):
    """
    Enhanced version: aggregates flow, adds logging, handles errors gracefully.
    """
    
    # Check rate limit
    if not await rate_limiter.check_limit(client_ip):
        wait_time = await rate_limiter.get_wait_time()
        error_msg = f"Rate limit exceeded. Try again in {wait_time:.1f}s"
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
        yield "data: [DONE]\n\n"
        return

    full_content = ""
    reasoning_content = ""
    response_id = None
    created_time = None
    model_name = None
    finish_reason = None
    usage = None
    tokens_received = 0
    
    # Timing
    start_time = time.time()
    first_token_time = None
    
    # Stats tracking
    debug_log = []

    try:
        async with httpx.AsyncClient(timeout=Config.TIMEOUT_SECONDS) as client:
            async with client.stream(
                "POST",
                f"{Config.REAL_BASE}/v1/chat/completions",
                headers={"Authorization": f"Bearer {Config.API_KEY}"},
                json=body,
            ) as resp:
                
                # Handle HTTP errors
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"Upstream API error: {error_text.decode()}"
                    )

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    data_str = line[len("data:") :].strip()
                    if not data_str or data_str == "[DONE]":
                        if data_str == "[DONE]":
                            break
                        continue

                    try:
                        chunk = json.loads(data_str)
                        if Config.DEBUG_MODE:
                            debug_log.append(f"Chunk: {json.dumps(chunk, indent=2)}")
                    except json.JSONDecodeError as e:
                        if Config.DEBUG_MODE:
                            print(f"⚠️ JSON parse error: {e}")
                        continue

                    # Record first token timing
                    if first_token_time is None:
                        first_token_time = time.time()

                    if not response_id:
                        response_id = chunk.get("id")
                        created_time = chunk.get("created")
                        model_name = chunk.get("model")

                    # Extract usage even when choices is empty (LongCat-2.0 sends usage in final chunk with empty choices)
                    if u := chunk.get("usage"):
                        usage = u

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    if delta := choice.get("delta"):
                        if content_part := delta.get("content"):
                            full_content += content_part
                            tokens_received += 1
                        
                        # Process reasoning for LongCat-2.0
                        if body.get("model") == Config.MODEL_NAME:
                            if reasoning_part := delta.get("reasoning_content"):
                                reasoning_content += reasoning_part

                    if fr := choice.get("finish_reason"):
                        finish_reason = fr

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
        error_response = {
            "id": f"error_{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": body.get("model"),
            "choices": [{
                "index": 0,
                "delta": {"content": f"\n\n[Proxy Error] {e.response.status_code}: {e.response.text}\n"},
                "finish_reason": "error"
            }]
        }
        yield f"data: {json.dumps(error_response)}\n\n"
        yield "data: [DONE]\n\n"
        return

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        error_response = {
            "id": f"error_{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": body.get("model"),
            "choices": [{
                "index": 0,
                "delta": {"content": f"\n\n[Proxy Internal Error] {str(e)}\n"},
                "finish_reason": "error"
            }]
        }
        yield f"data: {json.dumps(error_response)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # No data received
    if not response_id:
        print("❌ No data received from upstream")
        yield "data: [DONE]\n\n"
        return

    # ========== Statistics calculation ==========
    end_time = time.time()
    total_time = end_time - start_time
    time_to_first_token = (first_token_time - start_time) if first_token_time else 0
    
    # Token counting
    if usage:
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
    else:
        input_tokens = estimate_tokens(body.get("messages", [{"content": ""}])[-1].get("content", ""))//4  # Rough
        output_tokens = tokens_received or estimate_tokens(full_content)
        total_tokens = input_tokens + output_tokens
    
    # Speed
    processing_speed = (output_tokens / total_time) if total_time > 0 else 0
    
    # Compact single-line stats
    print(f"INFO:     {model_name or body.get('model')} | Tokens: {total_tokens} ↑{input_tokens} ↓{output_tokens} | {time_to_first_token*1000:.0f} ms to first token | {processing_speed:.0f} tok/sec | {total_time:.2f}s total")

    # ========== Build response ==========
    final_content = ""
    # Add hidden reasoning if enabled
    if (body.get("model") == Config.MODEL_NAME and 
        Config.SHOW_THINKING and 
        reasoning_content):
        final_content += f"<details><summary>🧠 Reasoning:</summary>\n\n{reasoning_content}\n\n</details>\n\n"
    final_content += full_content

    # Single chunk for Xcode compatibility
    chunk_data = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": model_name or body.get("model"),
        "choices": [{
            "index": 0,
            "delta": {"content": final_content},
            "finish_reason": finish_reason or "stop",
        }],
        "usage": usage or {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    }

    yield f"data: {json.dumps(chunk_data)}\n\n"
    await asyncio.sleep(0.01)
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, client_ip: Optional[str] = None):
    """
    Main endpoint: proxies to LongCat-2.0 with enhanced error handling and rate limiting.
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Sanitize and validate
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be JSON object")

    # Get client IP for rate limiting
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Validate model (case-insensitive, but always send correct case to API)
    requested_model = body.get("model", Config.MODEL_NAME)
    if requested_model.lower() != Config.MODEL_NAME.lower():
        print(f"⚠️ Unknown model '{requested_model}', defaulting to {Config.MODEL_NAME}")
    body["model"] = Config.MODEL_NAME  # Always use correct case for API

    # Force stream mode
    body["stream"] = True
    body["max_tokens"] = Config.MAX_TOKENS
    
    # LongCat-2.0: configure thinking mode
    # By default thinking is disabled for Xcode compatibility
    if "thinking" not in body:
        body["thinking"] = {"type": "enabled" if Config.THINKING_ENABLED else "disabled"}
    
    return StreamingResponse(
        stream_aggregator(body, client_ip),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ---------- Error Handlers ----------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"}
    )


# ---------- CLI Entry Point ----------
if __name__ == "__main__":
    import uvicorn
    
    # Log startup info
    print("=" * 60)
    print("🚀 LongCat-Xcode Bridge v0.2.0")
    print("=" * 60)
    print(f"📍 Base URL: {Config.REAL_BASE}")
    print(f"🔐 API Key: {'✓ Configured' if Config.API_KEY else '❌ MISSING'}")
    print(f"🔧 Debug: {Config.DEBUG_MODE}")
    print(f"🧠 Show Thinking: {Config.SHOW_THINKING}")
    print("=" * 60)
    
    if not Config.API_KEY:
        print("\n❌ Cannot start without API key!")
        exit(1)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG_MODE,
        log_level="debug" if Config.DEBUG_MODE else "info"
    )
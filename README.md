# LongCat-Xcode Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/OleksiyM/longcat-xcode-bridge/releases)

> ⚠️ **Important Update (July 1, 2026)**
> 
> As of June 30, 2026, LongCat API has moved to a paid model. Free quotas are no longer available.
> Legacy models (`longcat-flash-thinking`, `longcat-flash-chat`, etc.) have been retired.
> Only the **LongCat-2.0** model is now available, with trillion parameters and 1M context.
> 
> To use the API, you must set up billing:
> - **Token Pack** — fixed token quota valid for 30 days
> - **Pay-As-You-Go** — pay for actual usage
> 
> See: [LongCat ChangeLog](https://longcat.chat/platform/docs/ChangeLog.html)

A lightweight proxy server that makes the LongCat API (specifically the `LongCat-2.0` model) compatible with Xcode 26's local AI model feature.

## The Problem

Xcode 26's Intelligence AI mode feature requires an API endpoint that lists available models (typically `/v1/models`). The LongCat API does not provide this, making direct integration impossible.

## The Solution

This bridge acts as a middleman:
1.  It exposes a fake `/v1/models` endpoint to satisfy Xcode's requirement.
2.  It proxies requests from Xcode to the real LongCat API.
3.  It cleverly aggregates the streaming response from LongCat into a single chunk that Xcode can understand, overcoming compatibility issues with how Xcode handles streams.

## Features

-   **Xcode 26 Compatibility:** Enables the use of `LongCat-2.0` directly within Xcode.
-   **Zero-Configuration:** Works out of the box by setting one environment variable.
-   **Lightweight & Fast:** Built with FastAPI and Uvicorn for minimal overhead.
-   **Stream Aggregation:** Intelligently handles API stream differences between LongCat and Xcode.
-   **Enhanced Statistics:** Displays detailed performance metrics in the terminal including model name, token counts, response times, and processing speed.

## Prerequisites

-   Python 3.10+
-   `uv` (a fast Python package installer and resolver)
-   A LongCat API Key with active billing

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/OleksiyM/longcat-xcode-bridge.git
    cd longcat-xcode-bridge
    ```

2.  **Get your LongCat API Key:**
    -   Register or log in at [longcat.chat](https://longcat.chat).
    -   Navigate to the [API Keys page](https://longcat.chat/platform/api_keys) and generate a new key.
    -   **Important:** Set up billing (Token Pack or Pay-As-You-Go) as free quotas are no longer available.

3.  **Set the Environment Variable:**
    Replace `your_api_key_here` with the key you just generated.

    **macOS / Linux:**
    ```bash
    export LONGCAT_API_KEY='your_api_key_here'
    ```
    *(To make this permanent, add the line to your `~/.zshrc`, `~/.bash_profile`, or shell configuration file.)*

    **Windows (Command Prompt):**
    ```cmd
    set LONGCAT_API_KEY=your_api_key_here
    ```

## Running the Server

Two versions are available:

- **`main.py`** (recommended) — enhanced version with rate limiting, health checks, and advanced error handling
- **`main_legacy.py`** — minimal version with basic functionality only

Simply run the following command in the project directory:

```bash
uv run main.py
```

`uv` will automatically create a virtual environment and install the required dependencies (`fastapi`, `uvicorn`, `httpx`). The server will start on `http://0.0.0.0:8000`.

## Xcode Configuration

1.  In Xcode, go to **Settings > Intelligence**.
2.  Click the **+** button at the bottom of the providers list and select **Locally Hosted...**.
3.  For the **Port**, enter `8000`.
4.  Give it a descriptive name, like "Local LongCat Bridge".
5.  Click **Add**.

You can now select the `LongCat-2.0` model for code completion and other Intelligence features in Xcode.

## Statistics Output

The bridge displays compact performance metrics in the terminal for each request:

```
INFO:     LongCat-2.0 | Tokens: 3531 ↑1362 ↓2169 | 3326 ms to first token | 103 tok/sec | 20.96s total
```

The statistics include:
- **Model name** used for the request
- **Token counts**: Total tokens, input tokens (↑), and output tokens (↓)
- **Time to first token**: How long it took to receive the first response
- **Processing speed**: Tokens per second
- **Total time**: Overall request duration

## Billing Information

As of June 30, 2026, LongCat API requires active billing. Free quotas are no longer available.

Two billing options are available:

1.  **Token Pack:** Purchase a fixed Token quota upfront, valid for 30 calendar days from the date of purchase. Ideal for short-term, high-volume usage.
2.  **API Pay-As-You-Go:** Top up your balance and get charged based on actual Token consumption. Perfect for variable workloads or teams looking to keep costs under tight control.

Learn more at the [LongCat Platform Documentation](https://longcat.chat/platform/docs/ChangeLog.html).

## About LongCat & Useful Links

LongCat-2.0 is a state-of-the-art large language model developed by Meituan with the following core features:

- **Trillion Parameters, 1M Long Context:** Native tool calling and multi-step reasoning, reliably supporting long-context agent tasks.
- **Superior Coding Capability:** Excels in code generation, code understanding, and automated programming tasks.
- **Deeply Compatible with Claude Code and Other Mainstream Dev Environments:** Works efficiently with Claude Code, Hermes, OpenClaw, OpenCode and Kilo Code.

Here are some official links to learn more:

-   **[LongCat Platform](https://longcat.chat/):** The official LongCat website.
-   **[Platform Documentation](https://longcat.chat/platform/docs/):** Official guides and documentation for the LongCat platform.
-   **[API Usage Dashboard](https://longcat.chat/platform/usage/):** Monitor your API token usage.
-   **[ChangeLog](https://longcat.chat/platform/docs/ChangeLog.html):** Latest updates and changes to the LongCat API.

---

## Legacy Information (Deprecated)

### 🎁 Free tier (deprecated)

> **Note:** This information is outdated. As of June 30, 2026, free quotas are no longer available.

500k tokens/day by default; [You can visit the Usage to apply for an increase in your free tokens quota](https://longcat.chat/platform/usage) and get **5M tokens/day** for free while the beta lasts.

### Legacy models (deprecated)

> **Note:** These models were retired on May 29, 2026.

Previously, this bridge supported the following models:
- `longcat-flash-thinking` — deep reasoning model
- `longcat-flash-chat` — fast model for general tasks

For more information about the old models, see:
-   **[LongCat-Flash-Thinking on Hugging Face](https://huggingface.co/meituan-longcat/LongCat-Flash-Thinking)**
-   **[LongCat-Flash-Chat on Hugging Face](https://huggingface.co/meituan-longcat/LongCat-Flash-Chat)**
-   **[LongCat on GitHub](https://github.com/meituan-longcat)**

---

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Apple Inc. or the LongCat team. It is an independent tool for personal and community use.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# LongCat-Xcode Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Free Quota: 500k tokens/day](https://img.shields.io/badge/Free%20Quota-500k%20tokens%2Fday-brightgreen)](https://longcat.chat/platform/usage)

A lightweight proxy server that makes the LongCat API (specifically the `longcat-flash-thinking` and `longcat-flash-chat` models) compatible with Xcode 26's local AI model feature.

## The Problem

Xcode 26's Intelligence AI mode feature requires an API endpoint that lists available models (typically `/v1/models`). The LongCat API does not provide this, making direct integration impossible.

## The Solution

This bridge acts as a middleman:
1.  It exposes a fake `/v1/models` endpoint to satisfy Xcode's requirement.
2.  It proxies requests from Xcode to the real LongCat API.
3.  It cleverly aggregates the streaming response from LongCat into a single chunk that Xcode can understand, overcoming compatibility issues with how Xcode handles streams.

## Features

-   **Xcode 26 Compatibility:** Enables the use of `longcat-flash-thinking` and `longcat-flash-chat` directly within Xcode.
-   **Zero-Configuration:** Works out of the box by setting one environment variable.
-   **Lightweight & Fast:** Built with FastAPI and Uvicorn for minimal overhead.
-   **Stream Aggregation:** Intelligently handles API stream differences between LongCat and Xcode.
-   **Enhanced Statistics:** Displays detailed performance metrics in the terminal including model name, token counts, response times, and processing speed.

## Prerequisites

-   Python 3.10+
-   `uv` (a fast Python package installer and resolver)
-   A LongCat API Key

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/OleksiyM/longcat-xcode-bridge.git
    cd longcat-xcode-bridge
    ```

2.  **Get your LongCat API Key:**
    -   Register or log in at [longcat.chat](https://longcat.chat).
    -   Navigate to the [API Keys page](https://longcat.chat/platform/api_keys) and generate a new key.

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

You can now select either the `longcat-flash-thinking` or `longcat-flash-chat` models for code completion and other Intelligence features in Xcode.

## Statistics Output

The bridge displays detailed performance metrics in the terminal for each request:

```
INFO:     LongCat-Flash-Thinking | Tokens: 3531 ↑1362 ↓2169 | 3326 ms to first token | 103 tok/sec | 20.96s total
```

The statistics include:
- **Model name** used for the request
- **Token counts**: Total tokens, input tokens (↑), and output tokens (↓)
- **Time to first token**: How long it took to receive the first response
- **Processing speed**: Tokens per second
- **Total time**: Overall request duration

## 🎁 Free tier update

500k tokens/day by default; [You can visit the Usage to apply for an increase in your free tokens quota](https://longcat.chat/platform/usage) and get **5M tokens/day** for free while the beta lasts.

## About LongCat & Useful Links

For those unfamiliar, LongCat is a family of large language models developed by Meituan. They are designed to be powerful, efficient, and capable of handling a wide range of tasks. This bridge specifically uses the `longcat-flash-thinking` and `longcat-flash-chat` models, which are optimized for speed and code-related tasks.

Here are some official links to learn more:

-   **[LongCat on GitHub](https://github.com/meituan-longcat):** The official source code and repositories.
-   **[LongCat-Flash-Thinking on Hugging Face](https://huggingface.co/meituan-longcat/LongCat-Flash-Thinking):** The official model page for LongCat-Flash-Thinking.
-   **[LongCat-Flash-Chat on Hugging Face](https://huggingface.co/meituan-longcat/LongCat-Flash-Chat):** The official model page for LongCat-Flash-Chat.
-   **[Platform Documentation](https://longcat.chat/platform/docs/):** Official guides and documentation for the LongCat platform.
-   **[API Usage Dashboard](https://longcat.chat/platform/usage/):** Monitor your API token usage.

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Apple Inc. or the LongCat team. It is an independent tool for personal and community use.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
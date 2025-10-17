# LongCat-Xcode Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight proxy server that makes the LongCat API (specifically the `longcat-flash-thinking` model) compatible with Xcode 26's local AI model feature.

## The Problem

Xcode 26's Inelligence AI mode feature requires an API endpoint that lists available models (typically `/v1/models`). The LongCat API does not provide this, making direct integration impossible.

## The Solution

This bridge acts as a middleman:
1.  It exposes a fake `/v1/models` endpoint to satisfy Xcode's requirement.
2.  It proxies requests from Xcode to the real LongCat API.
3.  It cleverly aggregates the streaming response from LongCat into a single chunk that Xcode can understand, overcoming compatibility issues with how Xcode handles streams.

## Features

-   **Xcode 26 Compatibility:** Enables the use of `longcat-flash-thinking` directly within Xcode.
-   **Zero-Configuration:** Works out of the box by setting one environment variable.
-   **Lightweight & Fast:** Built with FastAPI and Uvicorn for minimal overhead.
-   **Stream Aggregation:** Intelligently handles API stream differences between LongCat and Xcode.

## Prerequisites

-   Python 3.8+
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

You can now select the `longcat-flash-thinking` model for code completion and other Intelligence features in Xcode.

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Apple Inc. or the LongCat team. It is an independent tool created for personal and community use.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
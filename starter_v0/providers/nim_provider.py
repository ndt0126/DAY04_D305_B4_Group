from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class NIMProvider(OpenAIProvider):
    """NVIDIA NIM exposes an OpenAI-compatible Chat Completions surface.

    Requires a model that supports function calling. The default is a
    reasoning-tuned model, which is accurate but noticeably slower per call;
    `meta/llama-3.3-70b-instruct` is a faster non-reasoning alternative.
    Override per-run with `--model`, or globally with the `NIM_MODEL` env var.
    """

    def __init__(self) -> None:
        super().__init__(
            api_key_env="NVIDIA_API_KEY",
            base_url=os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            default_model=os.getenv("NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1.5"),
        )

"""LLM 客户端 — OpenAI 兼容接口封装。

支持通过 .env 配置 OPENAI_API_KEY / OPENAI_BASE_URL / MANIMIND_MODEL。
提供普通聊天和结构化输出两种模式。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

try:
    from openai import OpenAI, APIError, APIConnectionError, RateLimitError
except ImportError:
    raise ImportError(
        "openai package is required. Install with: pip install openai"
    )


class LlmClient:
    """基于 .env 配置的 LLM 客户端。

    环境变量:
        - OPENAI_API_KEY: API 密钥（必需）
        - OPENAI_BASE_URL: API 基础 URL（可选，默认使用 OpenAI 官方）
        - MANIMIND_MODEL: 模型名称（可选，默认 gpt-4o）

    用法:
        client = LlmClient()
        response = client.chat(system_prompt="...", user_message="...")
        structured = client.chat_structured(..., output_schema={...})
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """初始化 LLM 客户端。

        Args:
            api_key: OpenAI API Key，默认从 .env 读取 OPENAI_API_KEY
            base_url: API 基础 URL，默认从 .env 读取 OPENAI_BASE_URL
            model: 模型名称，默认从 .env 读取 MANIMIND_MODEL， fallback 到 gpt-4o
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("MANIMIND_MODEL", "gpt-4o")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in .env file "
                "or pass it explicitly to LlmClient()."
            )

        # 初始化 OpenAI 客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self._client = OpenAI(**client_kwargs)

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送普通聊天请求。

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数（0.0-2.0），越低越确定
            max_tokens: 最大生成 token 数

        Returns:
            LLM 返回的文本响应

        Raises:
            RuntimeError: 当 LLM 调用失败且重试耗尽时
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise RuntimeError("LLM returned empty response")

                return content

            except (APIConnectionError, RateLimitError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # 指数退避
                    time.sleep(wait_time)
                continue

            except APIError as e:
                raise RuntimeError(f"LLM API error: {e}") from e

        raise RuntimeError(
            f"LLM call failed after {self.max_retries} retries. Last error: {last_error}"
        )

    def chat_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """发送结构化输出请求（强制 JSON 格式）。

        使用 OpenAI 的 response_format 或 prompt engineering 确保输出为合法 JSON。

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            output_schema: JSON Schema 定义期望的输出结构

        Returns:
            解析后的字典对象

        Raises:
            RuntimeError: 当 LLM 调用失败或返回无效 JSON 时
        """
        # 在系统提示中强调 JSON 输出要求
        enhanced_system_prompt = (
            f"{system_prompt}\n\n"
            "IMPORTANT: You MUST respond with valid JSON only. "
            "Do not include any explanatory text before or after the JSON. "
            "The JSON must conform to this schema:\n"
            f"{json.dumps(output_schema, ensure_ascii=False, indent=2)}"
        )

        enhanced_user_message = (
            f"{user_message}\n\n"
            "Please respond with ONLY a valid JSON object. No markdown, no explanation."
        )

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": enhanced_user_message},
                    ],
                    temperature=0.1,  # 结构化输出使用低温度
                    max_tokens=8192,
                    response_format={"type": "json_object"},  # OpenAI JSON 模式
                )

                content = response.choices[0].message.content
                if content is None:
                    raise RuntimeError("LLM returned empty response")

                # 尝试解析 JSON
                try:
                    result = json.loads(content)
                    if not isinstance(result, dict):
                        raise ValueError(f"Expected dict, got {type(result).__name__}")
                    return result
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"Failed to parse LLM response as JSON: {e}\n"
                        f"Response preview: {content[:500]}"
                    ) from e

            except (APIConnectionError, RateLimitError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    time.sleep(wait_time)
                continue

            except APIError as e:
                raise RuntimeError(f"LLM API error: {e}") from e

        raise RuntimeError(
            f"Structured LLM call failed after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

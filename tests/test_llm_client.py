"""LLM 客户端单元测试。"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from manimind.llm.client import LlmClient


# ============================================================================
# Fixture: 模拟 OpenAI 响应
# ============================================================================


@pytest.fixture
def mock_openai_response():
    """创建一个模拟的 OpenAI 响应对象。"""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "测试响应"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_openai_json_response():
    """创建一个模拟的 OpenAI JSON 响应对象。"""
    import json

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps({"key": "value", "number": 42})
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


# ============================================================================
# 初始化测试
# ============================================================================


def test_llm_client_init_with_env():
    """测试从环境变量初始化 LLM 客户端。"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        client = LlmClient()
        assert client.api_key == "test-key"
        assert client.model == "gpt-4o"  # 默认模型


def test_llm_client_init_with_custom_params():
    """测试使用自定义参数初始化 LLM 客户端。"""
    client = LlmClient(
        api_key="custom-key",
        base_url="https://custom.api.com",
        model="gpt-3.5-turbo",
        max_retries=5,
    )
    assert client.api_key == "custom-key"
    assert client.base_url == "https://custom.api.com"
    assert client.model == "gpt-3.5-turbo"
    assert client.max_retries == 5


def test_llm_client_init_without_api_key():
    """测试缺少 API Key 时抛出异常。"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
            LlmClient()


# ============================================================================
# chat 方法测试
# ============================================================================


def test_chat_success(mock_openai_response):
    """测试普通聊天成功。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_openai_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        result = client.chat(system_prompt="系统提示", user_message="用户消息")

        assert result == "测试响应"
        mock_instance.chat.completions.create.assert_called_once()


def test_chat_with_temperature_and_max_tokens(mock_openai_response):
    """测试聊天时使用自定义温度和最大 token。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_openai_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        result = client.chat(
            system_prompt="系统提示",
            user_message="用户消息",
            temperature=0.7,
            max_tokens=2048,
        )

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 2048


def test_chat_retry_on_connection_error(mock_openai_response):
    """测试连接错误时的重试机制。"""
    from openai import APIConnectionError

    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        # 前两次失败，第三次成功
        mock_instance.chat.completions.create.side_effect = [
            APIConnectionError(message="Connection failed"),
            APIConnectionError(message="Connection failed"),
            mock_openai_response,
        ]
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key", max_retries=3, retry_delay=0.01)
        result = client.chat(system_prompt="系统提示", user_message="用户消息")

        assert result == "测试响应"
        assert mock_instance.chat.completions.create.call_count == 3


def test_chat_empty_response():
    """测试空响应时抛出异常。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")

        with pytest.raises(RuntimeError, match="empty response"):
            client.chat(system_prompt="系统提示", user_message="用户消息")


# ============================================================================
# chat_structured 方法测试
# ============================================================================


def test_chat_structured_success(mock_openai_json_response):
    """测试结构化输出成功。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_openai_json_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        result = client.chat_structured(
            system_prompt="系统提示",
            user_message="用户消息",
            output_schema=schema,
        )

        assert result == {"key": "value", "number": 42}
        assert isinstance(result, dict)


def test_chat_structured_invalid_json():
    """测试无效 JSON 响应时抛出异常。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这不是 JSON"
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        schema = {"type": "object"}

        with pytest.raises(RuntimeError, match="Failed to parse"):
            client.chat_structured(
                system_prompt="系统提示",
                user_message="用户消息",
                output_schema=schema,
            )


def test_chat_structured_non_dict_response():
    """测试非字典类型的 JSON 响应时抛出异常。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "[1, 2, 3]"  # 数组而非对象
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        schema = {"type": "object"}

        with pytest.raises(RuntimeError, match="Expected dict"):
            client.chat_structured(
                system_prompt="系统提示",
                user_message="用户消息",
                output_schema=schema,
            )


def test_chat_structured_uses_low_temperature(mock_openai_json_response):
    """测试结构化输出使用低温度。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_openai_json_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        schema = {"type": "object"}
        client.chat_structured(
            system_prompt="系统提示",
            user_message="用户消息",
            output_schema=schema,
        )

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.1


def test_chat_structured_uses_json_object_format(mock_openai_json_response):
    """测试结构化输出使用 json_object 格式。"""
    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_openai_json_response
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key")
        schema = {"type": "object"}
        client.chat_structured(
            system_prompt="系统提示",
            user_message="用户消息",
            output_schema=schema,
        )

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}


# ============================================================================
# 重试机制测试
# ============================================================================


def test_max_retries_exhausted():
    """测试重试次数耗尽时抛出异常。"""
    from openai import APIConnectionError

    with patch("manimind.llm.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = APIConnectionError(
            message="Always fails"
        )
        MockOpenAI.return_value = mock_instance

        client = LlmClient(api_key="test-key", max_retries=2, retry_delay=0.01)

        with pytest.raises(RuntimeError, match="failed after 2 retries"):
            client.chat(system_prompt="系统提示", user_message="用户消息")


# ============================================================================
# 集成测试（需要真实 API Key）
# ============================================================================


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY environment variable",
)
def test_real_api_call():
    """测试真实的 API 调用（仅在配置了 API Key 时运行）。"""
    client = LlmClient()
    result = client.chat(
        system_prompt="你是一个助手。",
        user_message="请回复'测试成功'。",
        temperature=0.1,
        max_tokens=10,
    )
    assert isinstance(result, str)
    assert len(result) > 0

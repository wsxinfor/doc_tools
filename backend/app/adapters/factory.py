import logging

from app.adapters.base import AIAdapter

logger = logging.getLogger(__name__)


def get_ai_adapter(
    provider: str,
    api_key: str,
    model_url: str = "",
    model_name: str = "",
) -> AIAdapter:
    """根据 provider 返回对应 Adapter 实例。

    Args:
        provider: 'qwen' 或 'openai'
        api_key: 已解密的 API Key（不在日志中打印）
        model_url: 自定义 base URL，空字符串使用默认
        model_name: 自定义模型名称，空字符串使用默认
    """
    if provider == "qwen":
        from app.adapters.qwen import QwenAdapter  # noqa: PLC0415
        return QwenAdapter(api_key=api_key, model_name=model_name or "qwen3.6-plus")
    if provider == "openai":
        from app.adapters.openai_adapter import OpenAIAdapter  # noqa: PLC0415
        return OpenAIAdapter(
            api_key=api_key,
            base_url=model_url or None,
            model_name=model_name or "gpt-4o-mini",
        )
    raise ValueError(f"Unknown AI provider: {provider}")

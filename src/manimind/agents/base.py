"""Agent 抽象基类与 LLM 客户端接口协议。"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..context_assembly import (
    PromptSectionCache,
    build_context_packet,
    build_default_prompt_sections,
)
from ..models import AgentMode, AgentProfile, ContextScope, PipelineStage, ProjectPlan


@runtime_checkable
class LlmClientProtocol(Protocol):
    """LLM 客户端必须实现的接口。

    支持 OpenAI 兼容 API，通过 .env 配置 OPENAI_API_KEY / OPENAI_BASE_URL。
    """

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str: ...

    def chat_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]: ...


class BaseAgent(ABC):
    """所有 Agent 的抽象基类。

    子类约定:
    - 必须设置 ``role_id`` 类属性（与 AgentProfile.id 匹配）
    - 必须实现 ``run()`` 方法
    - 可选覆盖 ``build_user_message()`` 构建阶段特定的用户指令

    生命周期::

        agent = ConcreteAgent(plan, llm_client, session_id)
        result = agent.run(stage, task_id)
        # result["success"] 表示是否成功，result["outputs"] 为产出清单
    """

    role_id: str

    def __init__(
        self,
        plan: ProjectPlan,
        llm_client: LlmClientProtocol | None = None,
        session_id: str = "default",
    ):
        self.plan = plan
        self.llm_client = llm_client
        self.session_id = session_id
        self._profile = self._resolve_profile()

    def _resolve_profile(self) -> AgentProfile:
        for p in self.plan.agent_profiles:
            if p.id == self.role_id:
                return p
        raise ValueError(
            f"AgentProfile not found for role_id={self.role_id!r}. "
            f"Available: {[p.id for p in self.plan.agent_profiles]}"
        )

    @property
    def profile(self) -> AgentProfile:
        return self._profile

    @property
    def mode(self) -> AgentMode:
        return self._profile.mode

    def build_system_prompt(self, stage: PipelineStage) -> list[str]:
        """调用 context_assembly 生成该角色在该阶段的系统提示词分段。"""
        packet = build_context_packet(
            plan=self.plan,
            role_id=self.role_id,
            stage=stage,
        )
        cache = PromptSectionCache()
        return cache.resolve(build_default_prompt_sections(packet))

    def get_context_packet(self, stage: PipelineStage) -> dict[str, Any]:
        """获取该角色在该阶段的原始上下文包。"""
        return build_context_packet(
            plan=self.plan,
            role_id=self.role_id,
            stage=stage,
        )

    @abstractmethod
    def run(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """执行 Agent 主逻辑。

        标准生命周期:
            1. 从 runtime 加载当前状态
            2. 组装 system prompt
            3. 构造 user message
            4. 调用 LLM
            5. 解析返回结果
            6. 写入 runtime（structured_write 模式）
            7. 返回结构化结果

        Returns:
            dict 至少包含 ``success: bool`` 和 ``outputs: list[str]``。
        """
        ...

    def build_user_message(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> str:
        """构建用户消息。子类按阶段覆盖以注入具体任务指令。"""
        return f"执行任务 {task_id}，当前阶段：{stage.value}。"

    # ------------------------------------------------------------------
    # 上下文读写 — 直接操作 runtime 文件系统
    # ------------------------------------------------------------------

    def _context_file_path(self, key: str, scope: ContextScope) -> Path:
        """将上下文 key 映射到 runtime 文件路径。"""
        if scope == ContextScope.LONG_TERM:
            base = Path(self.plan.runtime_layout.project_context_dir)
        else:
            base = Path(self.plan.runtime_layout.session_context_root) / self.session_id
        safe_name = key.replace(".", "-")
        return base / f"{safe_name}.json"

    def _read_context(self, key: str) -> Any | None:
        """从 runtime 读取指定 key 的上下文正文。

        先查长期上下文，再查当前会话的短期上下文。
        """
        for scope in (ContextScope.LONG_TERM, ContextScope.SHORT_TERM):
            path = self._context_file_path(key, scope)
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                return payload.get("content") if isinstance(payload, dict) else payload
        return None

    def _write_context(
        self,
        key: str,
        content: Any,
        scope: ContextScope = ContextScope.LONG_TERM,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """向 runtime 写入上下文正文。

        仅 structured_write 和 verify_only 模式允许写入长期上下文。
        read_only 模式只能写入短期上下文（建议稿）。
        """
        if scope == ContextScope.LONG_TERM and self.mode == AgentMode.READ_ONLY:
            raise PermissionError(
                f"Agent {self.role_id} is READ_ONLY, cannot write to long-term context. "
                f"Use scope=SHORT_TERM for suggestion drafts."
            )

        path = self._context_file_path(key, scope)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "key": key,
            "scope": scope.value,
            "writer_role": self.role_id,
            "session_id": self.session_id,
            "content": content,
        }
        if metadata:
            payload["metadata"] = metadata

        tmp_path = path.with_name(f".{path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(path)
        return path

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _require_llm(self) -> LlmClientProtocol:
        """确保 LLM 客户端已注入，否则抛出明确错误。"""
        if self.llm_client is None:
            raise RuntimeError(
                f"Agent {self.role_id} requires an LLM client but none was provided. "
                f"Pass llm_client=LlmClient() when constructing the agent."
            )
        return self.llm_client

    def _stage_allowed(self, stage: PipelineStage) -> bool:
        """检查当前角色是否允许在给定阶段运行。"""
        return stage in self._profile.allowed_stages

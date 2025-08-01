# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
from collections.abc import Sequence
from typing import Literal

from beeai_framework.agents.experimental.requirements.requirement import Requirement, Rule
from beeai_framework.agents.experimental.types import RequirementAgentRequest, RequirementAgentRunState
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_framework.context import RunContext
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import AnyTool
from beeai_framework.tools.tool import Tool
from beeai_framework.utils.lists import remove_by_reference


class RequirementsReasoner:
    def __init__(
        self,
        *,
        tools: Sequence[AnyTool],
        final_answer: FinalAnswerTool,
        context: RunContext,
    ) -> None:
        self._tools = [*tools, final_answer]
        self._entries: list[Requirement[RequirementAgentRunState]] = []
        self._context = context
        self.final_answer = final_answer

    async def update(self, requirements: Sequence[Requirement[RequirementAgentRunState]]) -> None:
        self._entries.clear()

        for requirement in requirements:
            self._entries.append(requirement)

        for entry in self._entries:
            await entry.init(tools=self._tools, ctx=self._context)

    def _find_tool_by_name(self, name: str) -> AnyTool:
        tool: AnyTool | None = next((t for t in self._tools if t.name == name), None)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found in ({','.join(t.name for t in self._tools)}).")
        return tool

    async def create_request(
        self,
        state: RequirementAgentRunState,
        *,
        force_tool_call: bool,
        extra_rules: list[Rule] | None = None,
    ) -> RequirementAgentRequest:
        hidden: list[AnyTool] = []
        allowed: list[AnyTool] = []
        all_tools: list[AnyTool] = list(self._tools)

        prevent_stop: bool = False
        forced: AnyTool | None = None
        forced_level: int = 0
        rules_by_tool: dict[str, list[tuple[Rule, int]]] = {t.name: [] for t in self._tools}

        # Group rules
        for entry in [entry for entry in self._entries if entry.enabled]:
            requirements = await entry.run(state)
            for rule in requirements:
                tool = self._find_tool_by_name(rule.target)
                rules_by_tool[tool.name].append((rule, entry.priority))

        # Add extra rules
        for rule in extra_rules or []:
            if rule.target not in rules_by_tool:
                raise ValueError(f"Tool '{rule.target}' not found.")

            rules = rules_by_tool[rule.target]
            priority = max(rules, key=lambda v: v[1])[1] + 1 if rules else 1
            rules.append((rule, priority))

        # Aggregate rules and infer the required tool
        for tool_name, rules in rules_by_tool.items():
            tool = self._find_tool_by_name(tool_name)
            rules.sort(key=lambda x: x[1], reverse=True)  # DESC

            max_priority = rules[0][1] if rules else 1
            is_allowed = True
            is_forced = False
            is_hidden = False
            is_prevent_stop = False

            for rule, _ in rules:
                if not rule.allowed:
                    is_allowed = False
                if rule.hidden:
                    is_hidden = True
                if rule.forced:
                    is_forced = True
                if rule.prevent_stop:
                    is_prevent_stop = True

            if is_allowed and hidden:
                is_allowed = False

            if is_allowed:
                allowed.append(tool)
                if is_forced and (not forced or forced_level < max_priority):
                    forced = tool
                    forced_level = max_priority
            if is_hidden:
                hidden.append(tool)
            if is_prevent_stop:
                prevent_stop = True

        if forced is not None:
            allowed.clear()
            allowed.append(forced)
            allowed.append(self.final_answer)

        if prevent_stop and not isinstance(forced, FinalAnswerTool):
            with contextlib.suppress(ValueError):
                remove_by_reference(allowed, self.final_answer)

        if not allowed:
            raise FrameworkError("Unknown state. Tools cannot be empty.")

        tool_choice: Literal["required"] | AnyTool = forced if forced is not None else "required"
        if len(allowed) == 1:
            tool_choice = allowed[0]

        return RequirementAgentRequest(
            tools=all_tools,
            allowed_tools=allowed,
            tool_choice=tool_choice if isinstance(tool_choice, Tool) or force_tool_call or prevent_stop else "auto",
            final_answer=self.final_answer,
            hidden_tools=hidden,
            can_stop=not prevent_stop,
        )

/**
 * Copyright 2025 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ToolMessage } from "@/backend/message.js";
import type { AnyTool } from "@/tools/base.js";
import { DefaultRunner } from "@/agents/bee/runners/default/runner.js";
import type { BeeParserInput, BeeRunOptions } from "@/agents/bee/types.js";
import { BeeAgent, BeeInput } from "@/agents/bee/agent.js";
import type { GetRunContext } from "@/context.js";
import {
  GraniteBeeAssistantPrompt,
  GraniteBeeSchemaErrorPrompt,
  GraniteBeeSystemPrompt,
  GraniteBeeToolErrorPrompt,
  GraniteBeeToolInputErrorPrompt,
  GraniteBeeToolNotFoundPrompt,
  GraniteBeeUserPrompt,
} from "@/agents/bee/runners/granite/prompts.js";
import { BeeToolNoResultsPrompt, BeeUserEmptyPrompt } from "@/agents/bee/prompts.js";
import { Cache } from "@/cache/decoratorCache.js";

export class GraniteRunner extends DefaultRunner {
  protected useNativeToolCalling = true;

  @Cache({ enumerable: false })
  public get defaultTemplates() {
    return {
      system: GraniteBeeSystemPrompt,
      assistant: GraniteBeeAssistantPrompt,
      user: GraniteBeeUserPrompt,
      schemaError: GraniteBeeSchemaErrorPrompt,
      toolNotFoundError: GraniteBeeToolNotFoundPrompt,
      toolError: GraniteBeeToolErrorPrompt,
      toolInputError: GraniteBeeToolInputErrorPrompt,
      // Note: These are from bee
      userEmpty: BeeUserEmptyPrompt,
      toolNoResultError: BeeToolNoResultsPrompt,
    };
  }

  static {
    this.register();
  }

  constructor(input: BeeInput, options: BeeRunOptions, run: GetRunContext<BeeAgent>) {
    super(input, options, run);

    run.emitter.on(
      "update",
      async ({ update, meta, memory, data }) => {
        if (update.key === "tool_output") {
          await memory.add(
            new ToolMessage(
              {
                type: "tool-result",
                result: update.value!,
                toolName: data.tool_name!,
                isError: !meta.success,
                toolCallId: "DUMMY_ID",
              },
              { success: meta.success },
            ),
          );
        }
      },
      {
        isBlocking: true,
      },
    );
  }

  protected createParser(tools: AnyTool[]) {
    const { parser } = super.createParser(tools);

    return {
      parser: parser.fork<BeeParserInput>((nodes, options) => ({
        options,
        nodes: {
          ...nodes,
          thought: { ...nodes.thought, prefix: "Thought:" },
          tool_name: { ...nodes.tool_name, prefix: "Tool Name:" },
          tool_input: { ...nodes.tool_input, prefix: "Tool Input:", isEnd: true, next: [] },
          final_answer: { ...nodes.final_answer, prefix: "Final Answer:" },
        },
      })),
    };
  }
}

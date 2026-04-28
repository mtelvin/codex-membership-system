# codex-membership-system
简易的会员系统

## Prompt Agent 转完整 Agent 工具

新增 `prompt_agent_converter.py`，用于把“prompt 型 agent 的 markdown 文件”转换成一个可直接落地的 agent 脚手架目录。生成内容包括：

- `agent.json`：基础元数据、工具列表、章节索引
- `AGENTS.md`：可执行的角色与行为规范
- `prompts/system.md`：抽取的系统提示词
- `prompts/context.md`：其余上下文内容

### 用法

```bash
python prompt_agent_converter.py <输入md> --out <输出目录> [--name agent-name]
```

### 示例

```bash
python prompt_agent_converter.py sample_prompt_agent.md --out output-agent --name customer-service-agent
```

执行后会在 `output-agent/` 下看到完整 agent 文件结构。

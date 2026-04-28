#!/usr/bin/env python3
"""Convert a prompt-style agent markdown file into a runnable agent scaffold.

The converter reads a single markdown document and generates:
1) agent.json            - basic metadata + discovered sections
2) AGENTS.md             - operating instructions for the agent
3) prompts/system.md     - extracted system prompt
4) prompts/context.md    - extracted context/spec sections

Example:
    python prompt_agent_converter.py input.md --out ./my-agent
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Section:
    title: str
    level: int
    lines: List[str]

    def content(self) -> str:
        return "\n".join(self.lines).strip()


def parse_sections(md_text: str) -> List[Section]:
    """Split markdown into heading-based sections.

    Content before the first heading is stored as a section named "intro".
    """
    sections: List[Section] = []
    current = Section(title="intro", level=0, lines=[])

    for line in md_text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if current.lines:
                sections.append(current)
            current = Section(title=match.group(2).strip(), level=len(match.group(1)), lines=[])
        else:
            current.lines.append(line)

    if current.lines:
        sections.append(current)

    return sections


def normalize_key(title: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return key or "untitled"


def pick_section(sections: List[Section], candidates: List[str]) -> str:
    names = {normalize_key(c): c for c in candidates}
    for sec in sections:
        sec_key = normalize_key(sec.title)
        if sec_key in names and sec.content():
            return sec.content()
    return ""


def build_manifest(agent_name: str, source: Path, sections: List[Section]) -> Dict[str, object]:
    tool_text = pick_section(sections, ["tools", "available tools", "tooling"])
    goals_text = pick_section(sections, ["goal", "goals", "objective", "objectives"])

    tools = []
    for line in tool_text.splitlines():
        cleaned = line.strip().lstrip("-*0123456789. ").strip()
        if cleaned:
            tools.append(cleaned)

    return {
        "name": agent_name,
        "version": "0.1.0",
        "source_markdown": str(source),
        "description": goals_text.splitlines()[0] if goals_text else "Generated from prompt markdown",
        "tools": tools,
        "sections": [
            {
                "title": sec.title,
                "level": sec.level,
                "file_key": normalize_key(sec.title),
            }
            for sec in sections
        ],
    }


def build_agents_md(agent_name: str, system_prompt: str, sections: List[Section]) -> str:
    if not system_prompt:
        system_prompt = (
            "你是一个可执行任务的智能体。请遵循目标、约束和输出格式，"
            "必要时先澄清再执行。"
        )

    section_list = "\n".join(f"- {sec.title}" for sec in sections if sec.title != "intro")
    return f"""# {agent_name}\n\n## Role\n{system_prompt.strip()}\n\n## Source Sections\n{section_list or '- (none)'}\n\n## Execution Policy\n1. 先理解用户目标，再制定步骤。\n2. 对不确定的信息要显式说明假设。\n3. 输出保持结构化（摘要 + 详细步骤 + 下一步建议）。\n4. 涉及高风险领域时，给出安全提示并建议人工复核。\n"""


def write_outputs(
    out_dir: Path,
    manifest: Dict[str, object],
    system_prompt: str,
    extra_context: str,
    sections: List[Section],
) -> None:
    prompts_dir = out_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "agent.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    (out_dir / "AGENTS.md").write_text(
        build_agents_md(str(manifest["name"]), system_prompt, sections), encoding="utf-8"
    )

    (prompts_dir / "system.md").write_text(system_prompt.strip() + "\n", encoding="utf-8")
    (prompts_dir / "context.md").write_text(extra_context.strip() + "\n", encoding="utf-8")


def convert(input_md: Path, out_dir: Path, name: str | None) -> Path:
    text = input_md.read_text(encoding="utf-8")
    sections = parse_sections(text)

    agent_name = name or input_md.stem.replace("_", "-")
    system_prompt = pick_section(
        sections,
        ["system", "system prompt", "prompt", "instruction", "instructions"],
    )
    context = "\n\n".join(
        f"## {sec.title}\n\n{sec.content()}"
        for sec in sections
        if normalize_key(sec.title)
        not in {"system", "system_prompt", "prompt", "instruction", "instructions"}
    )

    manifest = build_manifest(agent_name, input_md, sections)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_outputs(out_dir, manifest, system_prompt, context, sections)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert prompt markdown to complete agent scaffold")
    parser.add_argument("input", type=Path, help="Path to prompt-style markdown")
    parser.add_argument("--out", type=Path, default=Path("generated-agent"), help="Output directory")
    parser.add_argument("--name", type=str, default=None, help="Agent name override")
    args = parser.parse_args()

    out_path = convert(args.input, args.out, args.name)
    print(f"✅ Agent scaffold generated at: {out_path}")


if __name__ == "__main__":
    main()

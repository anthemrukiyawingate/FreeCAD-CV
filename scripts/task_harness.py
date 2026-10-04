"""Emit a bounded, self-contained agent task packet from the approved backlog."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tasks() -> dict[str, dict[str, object]]:
    tasks = json.loads((ROOT / 'handoff/tasks.json').read_text(encoding='utf-8'))
    return {task['id']: task for task in tasks}


def task_packet(task_id: str) -> str:
    tasks = load_tasks()
    if task_id not in tasks:
        raise ValueError(f'Unknown task: {task_id}')
    task = tasks[task_id]
    lines = [f'As a Senior AI Developer and QA Auditor, execute {task_id}.',
             '1) Define tests. 2) Implement logic adhering to the EajR Signature. '
             '3) Document interfaces. 4) Package for dynamic deployment. '
             '5) Provide a QA Falsification audit proving safe failure modes across the Linux/Windows IPC boundary.',
             '', 'Read README.md and handoff/DEVOPS_HANDOFF.md before execution.',
             'Work only within the owned outputs. Preserve other contributors\' files.',
             'Build environment team exclusively owns version control; DevOps exclusively owns deployment.',
             'Do not infer live CAD success or measured hardware fit from offline tests.', '']
    for field in ('sprint','owner','dependencies','inputs','outputs','falsification','acceptance','status'):
        lines.append(f'{field.title()}: {task[field]}')
    if 'DEMO' in task_id:
        lines += ['', 'Role: Senior Graphics Programmer. Create a single HTML5 document with a requestAnimationFrame loop, '
                  'Dynamic Resolution Scaling, and lerped UI interactions. Use a modular JavaScript closure accurately '
                  'simulating the phase math. Target 60 FPS and record device measurements rather than asserting a guarantee.']
    lines += ['', 'Return: changed paths, actual red/green test commands and output, interface contract, falsification outcomes, '
              'and unresolved acceptance gates. Use Python 3.12+ for automation, 3.11+ for native scripts; explicitly '
              'recompute FreeCAD before reading geometry. Never retry an uncertain mutation automatically.']
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', nargs='?', help='Task ID; omitted to list all tasks')
    args = parser.parse_args()
    try:
        if args.task:
            print(task_packet(args.task))
        else:
            for task in load_tasks().values():
                print(f"{task['id']:16} Sprint {task['sprint']} · {task['owner']} · {task['status']}")
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

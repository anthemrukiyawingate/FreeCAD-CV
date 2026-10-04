from __future__ import annotations
import unittest
from scripts.task_harness import load_tasks, task_packet

class TaskHarnessTests(unittest.TestCase):
    def test_all_five_sprints_have_concrete_packets(self) -> None:
        tasks = load_tasks()
        self.assertEqual({task['sprint'] for task in tasks.values()}, {0, 1, 2, 3, 4})
        for task in tasks.values():
            for field in ('owner','inputs','outputs','falsification','acceptance','dependencies'):
                self.assertIn(field, task)
            self.assertTrue(task['outputs'])
            self.assertTrue(task['falsification'])

    def test_packet_contains_test_first_protocol_and_external_gate(self) -> None:
        packet = task_packet('S4-FIT')
        self.assertIn('1) Define tests.', packet)
        self.assertIn('DevOps', packet)
        self.assertIn('pending', packet.lower())

    def test_unknown_task_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            task_packet('not-a-task')

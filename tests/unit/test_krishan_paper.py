"""Structural tests for the deterministic paper (no root/system changes)."""

from unittest.mock import patch

from tasks.krishan_paper import PaperTask, ShellCheck, build_exam_tasks


EXPECTED_TASK_COUNT = 21
EXPECTED_MAX_SCORE = 275


def test_fixed_paper_shape():
    tasks = build_exam_tasks()
    assert len(tasks) == EXPECTED_TASK_COUNT
    assert len({task.id for task in tasks}) == len(tasks)
    assert all(task.difficulty == "exam" for task in tasks)
    assert sum(task.points for task in tasks) == EXPECTED_MAX_SCORE


def test_node_order():
    nodes = [task.node for task in build_exam_tasks()]
    assert nodes == [1] * 15 + [2] * 6


def test_exact_task_order_by_id():
    task_ids = [task.id for task in build_exam_tasks()]
    assert task_ids[0] == "n1_01_network_hostname"
    assert task_ids[14] == "n1_15_podman_container_service"
    assert task_ids[15] == "n2_01_root_password"
    assert task_ids[-1] == "n2_06_tuned"


def test_check_points_match_task_points():
    for task in build_exam_tasks():
        if task.checks_spec:
            assert sum(check.points for check in task.checks_spec) == task.points


def test_outcome_task_awards_partial_credit():
    task = PaperTask(
        "test", 1, "essential_tools", 10, "test", [
            ShellCheck("pass", 6, "true", "ok", "bad"),
            ShellCheck("fail", 4, "false", "ok", "bad"),
        ])
    with patch("tasks.krishan_paper._run", side_effect=[(0, ""), (1, "")]):
        result = task.validate()
    assert result.score == 6
    assert result.max_score == 10
    assert result.passed is False

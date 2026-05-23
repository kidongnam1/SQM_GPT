import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main_webview


def test_cleanup_removes_stale_project_process_before_single_instance_lock(monkeypatch):
    calls = []

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["59064"])
    monkeypatch.setattr(
        main_webview,
        "_get_process_command_line",
        lambda pid: rf'"C:\Python314\python.exe" "{main_webview.BASE_DIR}\main_webview.py"',
    )
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: False)
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: False)

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(main_webview.subprocess, "run", fake_run)

    assert main_webview.cleanup_stale_sqm_background_processes() is True
    assert calls == [["taskkill", "/F", "/PID", "59064"]]


def test_cleanup_preserves_visible_project_process(monkeypatch):
    calls = []

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["59064"])
    monkeypatch.setattr(
        main_webview,
        "_get_process_command_line",
        lambda pid: rf'"C:\Python314\python.exe" "{main_webview.BASE_DIR}\main_webview.py"',
    )
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: True)
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: False)
    def fake_run(args, **kwargs):
        if args and args[0] == "taskkill":
            calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(main_webview.subprocess, "run", fake_run)

    assert main_webview.cleanup_stale_sqm_background_processes() is False
    assert calls == []


def test_cleanup_ignores_unrelated_process_on_same_port(monkeypatch):
    calls = []

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["1234"])
    monkeypatch.setattr(
        main_webview,
        "_get_process_command_line",
        lambda pid: r'"C:\Python314\python.exe" "D:\other_app\main_webview.py"',
    )
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: False)
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: False)

    def fake_run(args, **kwargs):
        if args and args[0] == "taskkill":
            calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(main_webview.subprocess, "run", fake_run)

    assert main_webview.cleanup_stale_sqm_background_processes() is False
    assert calls == []


def test_cleanup_uses_local_settings_endpoint_when_command_line_is_unavailable(monkeypatch):
    calls = []

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["59064"])
    monkeypatch.setattr(main_webview, "_get_process_command_line", lambda pid: "")
    monkeypatch.setattr(main_webview, "_get_process_executable_path", lambda pid: "")
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: True)
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: False)

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(main_webview.subprocess, "run", fake_run)

    assert main_webview.cleanup_stale_sqm_background_processes() is True
    assert calls == [["taskkill", "/F", "/PID", "59064"]]


def test_cleanup_uses_windowless_python_on_sqm_port_as_last_resort(monkeypatch):
    calls = []

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["59064"])
    monkeypatch.setattr(main_webview, "_get_process_command_line", lambda pid: "")
    monkeypatch.setattr(main_webview, "_get_process_executable_path", lambda pid: r"C:\Python314\python.exe")
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: False)
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: False)

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(main_webview.subprocess, "run", fake_run)

    assert main_webview.cleanup_stale_sqm_background_processes() is True
    assert calls == [["taskkill", "/F", "/PID", "59064"]]


def test_cleanup_reports_false_when_taskkill_is_denied(monkeypatch):
    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(main_webview, "_pids_listening_on_port", lambda port: ["59064"])
    monkeypatch.setattr(main_webview, "_get_process_command_line", lambda pid: "")
    monkeypatch.setattr(main_webview, "_get_process_executable_path", lambda pid: r"C:\Python314\python.exe")
    monkeypatch.setattr(main_webview, "_port_serves_this_project_sqm", lambda: False)
    monkeypatch.setattr(main_webview, "_pid_has_visible_window", lambda pid: False)
    monkeypatch.setattr(
        main_webview.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 1, stderr="Access denied"),
    )

    assert main_webview.cleanup_stale_sqm_background_processes() is False


def test_select_available_api_port_skips_occupied_preferred_port(monkeypatch):
    occupied = {8765, 8766}

    monkeypatch.setattr(main_webview, "is_port_open", lambda host, port: port in occupied)

    assert main_webview.select_available_api_port() == 8767


def test_existing_instance_lock_can_be_ignored_when_no_visible_sqm_window(monkeypatch):
    monkeypatch.setattr(main_webview, "_acquire_single_instance_lock", lambda: False)
    monkeypatch.setattr(main_webview, "_visible_sqm_process_exists", lambda: False)

    assert main_webview.should_continue_after_single_instance_lock_failure() is True


def test_existing_instance_lock_is_honored_when_visible_sqm_window_exists(monkeypatch):
    monkeypatch.setattr(main_webview, "_acquire_single_instance_lock", lambda: False)
    monkeypatch.setattr(main_webview, "_visible_sqm_process_exists", lambda: True)

    assert main_webview.should_continue_after_single_instance_lock_failure() is False


def test_existing_instance_message_includes_actionable_fix_steps():
    msg = main_webview.existing_instance_resolution_message()

    assert "해결 방법" in msg
    assert "작업 관리자" in msg
    assert "taskkill /F /PID" in msg
    assert "netstat -ano | findstr" in msg

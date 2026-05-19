"""
SQM 전체 메뉴/사이드바/툴바 전수 UI 검사
======================================

빠른 smoke 검사는 `scripts/test_all_menus_playwright.py`가 담당하고,
이 스크립트는 릴리스 전 또는 큰 구조 변경 뒤에 더 넓게 훑는
exhaustive sweep 용도로 사용한다.

사용:
    python scripts/test_all_menu_actions_playwright.py --headless
    python scripts/test_all_menu_actions_playwright.py --standalone --headless
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 종료/복원/삭제/DB 변경처럼 전수 검사에서 자동 실행하면 안 되는 액션
SKIP_ACTIONS = {
    "onExit",
    "onRestore",
    "onOnBackup",
    "onApplyApproved",
    "onCleanupLogs",
    "onTestDbReset",
    "tb-backup",
}


def safe_print(*parts) -> None:
    text = " ".join(str(part) for part in parts)
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def close_modal_if_open(page) -> bool:
    modal = page.locator("#sqm-modal")
    if modal.count() and modal.is_visible():
        page.evaluate(
            """() => {
                const modal = document.getElementById('sqm-modal');
                if (modal) modal.style.display = 'none';
            }"""
        )
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--standalone", action="store_true", help="앱 자동 시작/종료")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    app_proc = None
    if args.standalone:
        safe_print("[1] 앱 시작 중...")
        app_proc = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "main_webview.py")],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(8)

    results: list[dict] = []
    errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page()
        page_errors: list[str] = []
        http_500: list[str] = []

        page.on("dialog", lambda dialog: dialog.dismiss())
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("response", lambda res: http_500.append(res.url) if res.status >= 500 else None)

        safe_print("[2] 페이지 접속...")
        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=15000)
        except Exception as exc:
            safe_print(f"접속 실패: {exc}")
            browser.close()
            if app_proc:
                app_proc.terminate()
            return 1

        safe_print("[3] 구조 검사...")
        top_menus = page.locator(".menu-btn[data-menu]")
        sidebar_routes = page.locator(".side-btn[data-route]").evaluate_all(
            "els => els.map(el => el.dataset.route)"
        )
        toolbar_actions = page.locator(".tool-btn[data-action]").evaluate_all(
            "els => els.map(el => el.dataset.action)"
        )
        all_actions = page.locator("[data-action]").evaluate_all(
            "els => [...new Set(els.map(el => el.dataset.action).filter(Boolean))]"
        )

        results.append(
            {
                "check": "top_menu_count",
                "pass": top_menus.count() >= 7,
                "actual": top_menus.count(),
            }
        )
        results.append(
            {
                "check": "sidebar_routes_present",
                "pass": len(sidebar_routes) >= 10,
                "actual": sidebar_routes,
            }
        )
        results.append(
            {
                "check": "toolbar_actions_present",
                "pass": len(toolbar_actions) >= 6,
                "actual": toolbar_actions,
            }
        )

        safe_print("[4] 사이드바 전수 클릭...")
        for route in sidebar_routes:
            before_page_errors = len(page_errors)
            before_http_500 = len(http_500)
            try:
                page.locator(f'.side-btn[data-route="{route}"]').first.click()
                page.wait_for_timeout(500)
                body_text = page.locator("body").inner_text().strip()
                page_container = page.locator("#page-container")
                dashboard = page.locator("#dashboard-container")
                visible_target = (
                    (page_container.count() and page_container.is_visible())
                    or (dashboard.count() and dashboard.is_visible())
                )
                ok = bool(body_text) and visible_target
                ok = ok and len(page_errors) == before_page_errors and len(http_500) == before_http_500
                results.append({"route": route, "pass": ok})
                if not ok:
                    errors.append(f"sidebar:{route}")
            except Exception as exc:
                results.append({"route": route, "pass": False, "error": str(exc)})
                errors.append(f"sidebar:{route}: {exc}")

        safe_print("[5] 모든 data-action 전수 클릭...")
        for action in all_actions:
            if action in SKIP_ACTIONS:
                results.append({"action": action, "pass": True, "skipped": True})
                continue

            before_page_errors = len(page_errors)
            before_http_500 = len(http_500)
            try:
                clicked = page.evaluate(
                    """(action) => {
                        const el = document.querySelector(`[data-action="${action}"]`);
                        if (!el) return false;
                        el.click();
                        return true;
                    }""",
                    action,
                )
                if not clicked:
                    raise RuntimeError("button not found")
                page.wait_for_timeout(450)
                body_text = page.locator("body").inner_text().strip()
                modal_opened = close_modal_if_open(page)
                ok = bool(body_text)
                ok = ok and len(page_errors) == before_page_errors and len(http_500) == before_http_500
                results.append({"action": action, "pass": ok, "modal": modal_opened})
                if not ok:
                    errors.append(f"action:{action}")
            except Exception as exc:
                results.append({"action": action, "pass": False, "error": str(exc)})
                errors.append(f"action:{action}: {exc}")

        browser.close()

    if app_proc:
        app_proc.terminate()
        try:
            app_proc.wait(timeout=5)
        except Exception:
            app_proc.kill()

    total = len(results)
    passed = sum(1 for item in results if item.get("pass"))
    failed = total - passed
    summary = {
        "total": total,
        "pass": passed,
        "fail": failed,
        "skipped": sum(1 for item in results if item.get("skipped")),
    }

    if page_errors:
        errors.append("PAGEERROR: " + " | ".join(page_errors))
    if http_500:
        errors.append("HTTP500: " + ", ".join(http_500))

    report_path = PROJECT_ROOT / "REPORTS" / "playwright_all_menu_actions.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "errors": errors,
                "skipped_actions": sorted(SKIP_ACTIONS),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    safe_print(f"결과: 총 {total}건 · PASS {passed} · FAIL {failed} · SKIP {summary['skipped']}")
    for err in errors:
        safe_print(" -", err)
    safe_print(f"결과 저장: {report_path}")

    return 0 if failed == 0 and not errors else 1


if __name__ == "__main__":
    sys.exit(main())

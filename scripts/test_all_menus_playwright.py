"""
SQM 핵심 UI smoke suite
======================

기존 스크립트는 모든 메뉴 액션을 광범위하게 클릭해 오래 걸리고
부작용 가능성도 컸다. 이 버전은 릴리스 전 빠르게 돌릴 수 있는
핵심 화면 smoke 검증만 수행한다.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTES = [
    "pending",
    "available",
    "allocation",
    "picked",
    "return",
    "move",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    results = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page()
        responses_500 = []
        page_errors = []

        page.on("response", lambda res: responses_500.append(res.url) if res.status >= 500 else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            page.goto(args.base_url, wait_until="networkidle", timeout=15000)
        except Exception as exc:
            print(f"접속 실패: {exc}")
            browser.close()
            return 1

        script_srcs = page.eval_on_selector_all("script[src]", "els => els.map(e => e.getAttribute('src'))")
        expected_assets = {
            "sqm-core.js": "20260517p22",
            "sqm-inline.js": "20260517p29",
            "sqm-upload-modals.js": "20260517a",
            "sqm-aux-modals.js": "20260517a",
            "sqm-tools-modals.js": "20260517a",
            "sqm-product-modals.js": "20260517a",
        }
        asset_versions = {}
        for src in script_srcs:
            if not src:
                continue
            name = src.split("/")[-1].split("?")[0]
            version = src.split("?v=")[-1] if "?v=" in src else ""
            if name in expected_assets:
                asset_versions[name] = version
        stale_assets = {
            name: {"expected": expected, "actual": asset_versions.get(name)}
            for name, expected in expected_assets.items()
            if asset_versions.get(name) != expected
        }
        results.append({"check": "asset_versions", "pass": not stale_assets, "detail": stale_assets or asset_versions})
        if stale_assets:
            errors.append("STALE_ASSETS: " + json.dumps(stale_assets, ensure_ascii=False))

        for route in ROUTES:
            try:
                btn = page.locator(f'[data-route="{route}"]').first
                btn.click()
                page.wait_for_timeout(350)
                text = page.locator("#page-container").inner_text()
                ok = bool(text.strip()) and "Preparing:" not in text
                results.append({"route": route, "pass": ok})
                if not ok:
                    errors.append(f"{route}: empty/preparing")
            except Exception as exc:
                results.append({"route": route, "pass": False, "error": str(exc)})
                errors.append(f"{route}: {exc}")

        # 타깃 기능 smoke
        page.locator('[data-route="available"]').first.click()
        page.wait_for_timeout(700)
        results.append({"check": "available_columns", "pass": "CON RETURN" in page.locator("#page-container").inner_text().upper()})

        page.locator('[data-route="move"]').first.click()
        page.wait_for_timeout(700)
        results.append({"check": "move_lot_input", "pass": page.locator("#move-lot-no").count() == 1})

        exports = page.evaluate("""() => ({
            upload: typeof window.showInboundManualUploadModal,
            upload_pdf: typeof window.showPickingListPdfModal,
            product: typeof window.showProductSummaryModal,
            tools: typeof window.showDocConvertModal,
            aux: typeof window.showAiToolsHubModal,
            info: typeof window.renderInfoModal,
        })""")
        results.append({"check": "module_exports", "pass": all(v == "function" for v in exports.values()), "detail": exports})

        modal_cases = [
            ("onInboundManual", "수동 입고"),
            ("onProductLotLookup", "품목별 LOT 조회"),
            ("onDocConvert", "문서 변환"),
            ("onAiTools", "AI / 선사 도구"),
        ]
        for action, expected_text in modal_cases:
            page.evaluate("(action) => window.SQM.dispatchAction(action)", action)
            page.wait_for_timeout(250)
            modal_text = page.locator("#sqm-modal-content").inner_text()
            ok = page.locator("#sqm-modal").is_visible() and expected_text in modal_text
            results.append({"check": f"modal_{action}", "pass": ok})
            page.evaluate("() => { document.getElementById('sqm-modal').style.display = 'none'; }")

        if responses_500:
            errors.append("HTTP500: " + ", ".join(responses_500))
        if page_errors:
            errors.append("PAGEERROR: " + " | ".join(page_errors))

        browser.close()

    total = len(results)
    passed = sum(1 for r in results if r.get("pass"))
    failed = total - passed
    print(f"결과: 총 {total}건 · PASS {passed} · FAIL {failed}")
    for err in errors:
        print(" -", err)

    out = PROJECT_ROOT / "REPORTS" / "playwright_ui_smoke.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        json.dumps(
            {"summary": {"total": total, "pass": passed, "fail": failed}, "errors": errors, "results": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0 if failed == 0 and not errors else 1


if __name__ == "__main__":
    sys.exit(main())

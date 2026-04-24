"""state キー衝突バグ修正の回帰テスト。

同一 URL を持つ複数監視サイト（SBI損保、ソニー損保など）が
lambda_handler で state のキーに URL を使っていたため互いに上書きし、
毎回同じ内容を Slack 通知してしまうバグを検証する。

実行方法（ローカル、sandbox どちらでも lxml/boto3 なしで動く）:
    python3 test_state_migration.py
"""
import json
import os
import sys
import pathlib
import types
from unittest.mock import patch

os.environ["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/TEST/TEST/TEST"
os.environ.pop("STATE_BUCKET", None)

# ---------------------------------------------------------------------------
# 依存ライブラリ（lxml / boto3）は lambda_function の import 時にだけ必要なので
# 最小のスタブを登録して import を通す。実ロジックは fetch_articles / send_slack
# をモックするので、これらの実装は必要ない。
# ---------------------------------------------------------------------------
if "lxml" not in sys.modules:
    lxml_mod = types.ModuleType("lxml")
    lxml_html_mod = types.ModuleType("lxml.html")
    lxml_html_mod.HtmlElement = object  # type: ignore[attr-defined]
    lxml_html_mod.fromstring = lambda *a, **k: None  # type: ignore[attr-defined]
    lxml_mod.html = lxml_html_mod  # type: ignore[attr-defined]
    sys.modules["lxml"] = lxml_mod
    sys.modules["lxml.html"] = lxml_html_mod
if "boto3" not in sys.modules:
    boto3_mod = types.ModuleType("boto3")
    boto3_mod.client = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["boto3"] = boto3_mod

SRC = pathlib.Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))

# extractors / sites 本体は lxml を使うので、テスト用のダミーに差し替える
extractors_stub = types.ModuleType("extractors")
extractors_stub.EXTRACTORS = {}
sys.modules["extractors"] = extractors_stub

sites_stub = types.ModuleType("sites")
sites_stub.SITES = []
sys.modules["sites"] = sites_stub

import lambda_function as lf  # noqa: E402


# ---------------------------------------------------------------------------
# ヘルパ
# ---------------------------------------------------------------------------

def run_lambda(state, site_to_articles, sites):
    """指定 state / モック記事 / SITES で lambda_handler を実行。
    戻り値: (新 state, [(site_name, new_articles), ...])
    """
    slack_calls = []

    def fake_slack(site_name, new_articles):
        slack_calls.append((site_name, [dict(a) for a in new_articles]))

    def fake_fetch(site):
        return site_to_articles.get(site["name"], [])

    with open("/tmp/PnC_insuranceNews_state.json", "w") as f:
        json.dump(state, f, ensure_ascii=False)

    with patch.object(lf, "fetch_articles", side_effect=fake_fetch), \
         patch.object(lf, "send_slack", side_effect=fake_slack), \
         patch.object(lf, "SITES", sites):
        lf.lambda_handler({}, None)

    with open("/tmp/PnC_insuranceNews_state.json") as f:
        new_state = json.load(f)
    return new_state, slack_calls


def eq(actual, expected, label):
    if actual != expected:
        print(f"  FAIL  {label}")
        print(f"    expected: {expected}")
        print(f"    actual:   {actual}")
        return False
    print(f"  PASS  {label}")
    return True


# ---------------------------------------------------------------------------
# テストケース
# ---------------------------------------------------------------------------

def test_same_url_independent():
    """バグ再現: 同じ URL の 2 サイトが独立に差分検知されること。"""
    sites = [
        {"name": "SBI ニュース", "url": "https://sbi.example.com/c/",
         "base_url": "https://sbi.example.com", "xpath": "dummy", "extractor": "dummy"},
        {"name": "SBI お知らせ", "url": "https://sbi.example.com/c/",
         "base_url": "https://sbi.example.com", "xpath": "dummy", "extractor": "dummy"},
    ]

    # 1回目: 初回ベースライン
    state, slack = run_lambda({},
        {"SBI ニュース": [{"href": "/n1", "title": "N1"}, {"href": "/n2", "title": "N2"}],
         "SBI お知らせ": [{"href": "/i1", "title": "I1"}]}, sites)
    ok = True
    ok &= eq(state, {"SBI ニュース": ["/n1", "/n2"], "SBI お知らせ": ["/i1"]},
             "初回: name キーで独立記録")
    ok &= eq(slack, [], "初回: 通知なし")

    # 2回目: ニュースに新記事1件
    state, slack = run_lambda(state,
        {"SBI ニュース": [{"href": "/n3", "title": "N3"}, {"href": "/n1", "title": "N1"}, {"href": "/n2", "title": "N2"}],
         "SBI お知らせ": [{"href": "/i1", "title": "I1"}]}, sites)
    ok &= eq(slack, [("SBI ニュース", [{"href": "/n3", "title": "N3"}])],
             "2回目: ニュースのみ通知")

    # 3回目: 変化なし（これが修正の核心 = 毎回同じ通知が来ないこと）
    state, slack = run_lambda(state,
        {"SBI ニュース": [{"href": "/n3", "title": "N3"}, {"href": "/n1", "title": "N1"}, {"href": "/n2", "title": "N2"}],
         "SBI お知らせ": [{"href": "/i1", "title": "I1"}]}, sites)
    ok &= eq(slack, [], "3回目: 差分なし → 通知なし（バグ修正の核心）")
    return ok


def test_old_state_duplicate_url_ignored():
    """旧 URL キー state が残っていても、同じ URL の 2 サイトは初回扱い（無駄な通知を防ぐ）。"""
    sites = [
        {"name": "SBI ニュース", "url": "https://sbi.example.com/c/",
         "base_url": "https://sbi.example.com", "xpath": "d", "extractor": "d"},
        {"name": "SBI お知らせ", "url": "https://sbi.example.com/c/",
         "base_url": "https://sbi.example.com", "xpath": "d", "extractor": "d"},
    ]
    old_state = {"https://sbi.example.com/c/": ["/i1"]}

    state, slack = run_lambda(old_state,
        {"SBI ニュース": [{"href": "/n1", "title": "N1"}],
         "SBI お知らせ": [{"href": "/i1", "title": "I1"}, {"href": "/i2", "title": "I2"}]}, sites)
    ok = True
    ok &= eq(slack, [], "旧 URL キー state: URL 重複サイトは初回扱い（通知しない）")
    ok &= eq(state, {"SBI ニュース": ["/n1"], "SBI お知らせ": ["/i1", "/i2"]},
             "新 name キーで state 書き込み")
    return ok


def test_old_state_unique_url_migrated():
    """URL が一意なサイトは、旧 URL キー state から移行して差分検知を継続。"""
    sites = [
        {"name": "単独サイト", "url": "https://solo.example.com/",
         "base_url": "https://solo.example.com", "xpath": "d", "extractor": "d"},
    ]
    old_state = {"https://solo.example.com/": ["/a", "/b"]}

    state, slack = run_lambda(old_state,
        {"単独サイト": [{"href": "/c", "title": "新記事"}, {"href": "/a", "title": "A"}, {"href": "/b", "title": "B"}]},
        sites)
    ok = True
    ok &= eq(slack, [("単独サイト", [{"href": "/c", "title": "新記事"}])],
             "旧 URL キー state → 一意 URL は差分検知継続")
    ok &= eq(state, {"単独サイト": ["/c", "/a", "/b"]}, "新 name キーで保存")
    return ok


def test_fetch_error_preserves():
    """fetch 失敗時は前回 state を保つ（欠損させない）。"""
    sites = [{"name": "サイトA", "url": "https://a.example.com/",
              "base_url": "https://a.example.com", "xpath": "x", "extractor": "d"}]
    prev = {"サイトA": ["/x", "/y"]}

    with patch.object(lf, "fetch_articles", side_effect=RuntimeError("network error")), \
         patch.object(lf, "send_slack") as mock_slack, \
         patch.object(lf, "SITES", sites):
        with open("/tmp/PnC_insuranceNews_state.json", "w") as f:
            json.dump(prev, f)
        lf.lambda_handler({}, None)
        with open("/tmp/PnC_insuranceNews_state.json") as f:
            state = json.load(f)

    ok = True
    ok &= eq(state, prev, "fetch エラー時、前回 state を保持")
    ok &= eq(mock_slack.call_count, 0, "fetch エラー時、Slack 通知なし")
    return ok


def test_sompo_direct_two_urls():
    """SOMPOダイレクト型（URL 異なるが内容が同じ可能性あり）。
    name で区別されるため、初回以降に差分がなければ通知されない。
    """
    sites = [
        {"name": "SOMPO 大切なお知らせ", "url": "https://news.example.com/?type=important",
         "base_url": "https://news.example.com", "xpath": "x", "extractor": "d"},
        {"name": "SOMPO ニュースリリース", "url": "https://news.example.com/?type=news",
         "base_url": "https://news.example.com", "xpath": "x", "extractor": "d"},
    ]

    state, _ = run_lambda({},
        {"SOMPO 大切なお知らせ": [{"href": "/t/1", "title": "T1"}],
         "SOMPO ニュースリリース": [{"href": "/t/1", "title": "T1"}]}, sites)
    state, slack = run_lambda(state,
        {"SOMPO 大切なお知らせ": [{"href": "/t/1", "title": "T1"}],
         "SOMPO ニュースリリース": [{"href": "/t/1", "title": "T1"}]}, sites)
    return eq(slack, [], "SOMPOダイレクト型: 同内容再実行で通知が繰り返されない")


def main():
    tests = [
        ("同一 URL の 2 サイトが独立に差分検知される", test_same_url_independent),
        ("旧 URL キー state: 重複 URL は初回扱い", test_old_state_duplicate_url_ignored),
        ("旧 URL キー state: 一意 URL は自動移行", test_old_state_unique_url_migrated),
        ("fetch エラー時は前回 state を保持", test_fetch_error_preserves),
        ("SOMPOダイレクト型 2URL の独立管理", test_sompo_direct_two_urls),
    ]
    passed = failed = 0
    for label, fn in tests:
        print(f"\n[TEST] {label}")
        try:
            if fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL  exception: {e}")
            import traceback; traceback.print_exc()
            failed += 1
    print(f"\n結果: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

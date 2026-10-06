"""对运行中的 diet_server 做接口冒烟测试。

用法:
    python test_api.py [base_url]     # 默认 http://127.0.0.1:8000
只用标准库，本地或容器里都能直接跑。
"""

import json
import sys
import urllib.error
import urllib.request

# Windows 控制台默认 GBK，直接 print 中文会乱码
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"

passed = failed = 0


def get(path: str) -> tuple[int, str, bytes]:
    """返回 (状态码, content-type, body)。4xx/5xx 不抛异常。"""
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", ""), e.read()


def check(name: str, path: str, want_status: int, want_json: dict | None = None):
    global passed, failed
    try:
        status, ctype, body = get(path)
    except Exception as e:
        print(f"  FAIL  {name:<28} 连接失败: {e}")
        failed += 1
        return

    problems = []
    if status != want_status:
        problems.append(f"状态码 {status} != {want_status}")
    if want_json is not None and "application/json" not in ctype:
        problems.append(f"content-type 是 {ctype!r}, 期望 json")
    if want_json is not None:
        try:
            got = json.loads(body)
        except json.JSONDecodeError:
            problems.append(f"响应不是合法 JSON: {body[:80]!r}")
        else:
            for k, v in want_json.items():
                if got.get(k) != v:
                    problems.append(f"{k}={got.get(k)!r} != {v!r}")

    if problems:
        print(f"  FAIL  {name:<28} {'; '.join(problems)}")
        failed += 1
    else:
        print(f"  ok    {name:<28} {status} {body[:70].decode(errors='replace')}")
        passed += 1


print(f"测试目标: {BASE}\n")

print("[业务接口]")
check("hello", "/api/hello", 200, {"message": "Hello, World!"})
check("health", "/api/health", 200, {"status": "ok", "service": "diet_server"})

print("\n[根路径与文档]")
check("root", "/", 200, {"service": "diet_server"})
check("openapi schema", "/openapi.json", 200)
check("swagger docs", "/docs", 200)

print("\n[错误处理]")
check("不存在的路径返回 404", "/api/nope", 404)

print(f"\n结果: {passed} 通过, {failed} 失败")
sys.exit(1 if failed else 0)

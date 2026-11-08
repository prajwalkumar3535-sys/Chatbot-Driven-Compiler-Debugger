import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
for p in [BACKEND_DIR, PROJECT_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.routers.run import run_code, RunRequest
from app.routers.models import get_health, get_languages, get_models, get_agents

def test_sync():
    print("[1] Testing Health...", flush=True)
    health = get_health()
    print("Health:", health, flush=True)

    print("\n[2] Testing Languages...", flush=True)
    langs = get_languages()
    print(f"Found {len(langs)} languages: {[l['id'] for l in langs]}", flush=True)

    print("\n[3] Testing Models...", flush=True)
    mods = get_models()
    print(f"Found {len(mods['models'])} models", flush=True)

    print("\n[4] Testing Agents...", flush=True)
    agents = get_agents()
    print(f"Found {len(agents)} agents: {[a['name'] for a in agents]}", flush=True)

    print("\n[5] Testing Execution (Python)...", flush=True)
    res = run_code(RunRequest(language="python", code="print(2 + 3)", stdin=""))
    print("Execution Result:", res.status, "Stdout:", res.stdout, "Time:", res.time_ms, "ms", "Eco:", res.eco_score, flush=True)
    assert res.status == "accepted" and "5" in res.stdout

    print("\n[6] Testing Execution (C++)...", flush=True)
    cpp_code = """
#include <iostream>
int main() {
    std::cout << "CPP Output: " << 10 * 5 << std::endl;
    return 0;
}
"""
    res_cpp = run_code(RunRequest(language="cpp", code=cpp_code, stdin=""))
    print("C++ Execution Result:", res_cpp.status, "Stdout:", res_cpp.stdout, "Time:", res_cpp.time_ms, "ms", flush=True)
    assert res_cpp.status == "accepted" and "50" in res_cpp.stdout

    print("\n[7] Testing AST Generator Integration...", flush=True)
    from app.ast_generator import generate_ast_analysis
    py_ast = generate_ast_analysis("def test_fn():\n    return 42", "python")
    assert py_ast["syntax_valid"] is True
    assert "test_fn" in py_ast["symbols"]["functions"]
    print("Python AST valid:", py_ast["symbols"]["functions"], flush=True)

    err_ast = generate_ast_analysis("def broken(a, b)\n    pass", "python")
    assert err_ast["syntax_valid"] is False
    assert err_ast["syntax_error"]["line"] == 1
    print("Python AST caught syntax error on line 1:", err_ast["syntax_error"]["message"], flush=True)

    print("\n[8] Testing Model Resolver...", flush=True)
    from app.ollama_client import resolve_best_model
    qwen_res = resolve_best_model("qwen")
    phi_res = resolve_best_model("phi3")
    llama_res = resolve_best_model("llama3")
    print(f"Resolved models -> Qwen: {qwen_res}, Phi: {phi_res}, Llama: {llama_res}", flush=True)
    assert qwen_res is not None and phi_res is not None and llama_res is not None

    print("\nALL BACKEND API UNIT TESTS PASSED!", flush=True)

if __name__ == "__main__":
    test_sync()

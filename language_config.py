"""
language_config.py - Centralized Language Configuration
Single source of truth for all language-specific execution settings.
The backend determines ALL execution parameters from this config.
The frontend may ONLY send a language key ('cpp', 'python', 'java').
"""

# ============================================================
# LANGUAGE REGISTRY - All allowed languages and their configs
# ============================================================
LANGUAGE_CONFIG = {
    "cpp": {
        "display_name":     "C++",
        "extension":        ".cpp",
        "source_filename":  "solution.cpp",
        "docker_image":     "cpp-sandbox",
        "compile_cmd":      "g++ -g /sandbox/solution.cpp -o /sandbox/prog_bin",
        "run_cmd":          "/sandbox/prog_bin",
        "needs_compile":    True,
        "compile_timeout":  12,     # seconds
        "run_timeout":      5,      # seconds
        "memory_limit":     "256m",
        "compile_memory":   "512m",
        "cpu_limit":        "1.0",
        "pids_limit":       32,
        "default_code": """\
#include <iostream>
using namespace std;

int main() {
    cout << "Hello from C++!" << endl;
    return 0;
}""",
    },

    "python": {
        "display_name":     "Python",
        "extension":        ".py",
        "source_filename":  "solution.py",
        "docker_image":     "python-sandbox",
        "compile_cmd":      None,                          # No compile step
        "run_cmd":          "python3 /sandbox/solution.py",
        "needs_compile":    False,
        "compile_timeout":  None,
        "run_timeout":      5,
        "memory_limit":     "256m",
        "compile_memory":   None,
        "cpu_limit":        "1.0",
        "pids_limit":       32,
        "default_code": """\
# Python Execution
print("Hello from Python!")
""",
    },

    "java": {
        "display_name":     "Java",
        "extension":        ".java",
        "source_filename":  "Main.java",
        "docker_image":     "java-sandbox",
        "compile_cmd":      "rm -f /sandbox/*.class; javac /sandbox/Main.java -d /sandbox",
        "run_cmd":          "java -cp /sandbox Main",
        "needs_compile":    True,
        "compile_timeout":  20,     # javac startup + compile
        "run_timeout":      5,
        "memory_limit":     "256m",
        "compile_memory":   "512m",
        "cpu_limit":        "1.0",
        "pids_limit":       64,     # JVM needs more threads
        "default_code": """\
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}
""",
    },
}

# Allowed language keys (whitelist - never accept anything outside this)
ALLOWED_LANGUAGES = set(LANGUAGE_CONFIG.keys())


def get_language_config(language: str) -> dict | None:
    if not isinstance(language, str):
        return None
    return LANGUAGE_CONFIG.get(language.lower().strip())


def validate_language(language: str) -> tuple[bool, str]:
    if not isinstance(language, str) or not language.strip():
        return False, "Language must be a non-empty string."
    if language.lower().strip() not in ALLOWED_LANGUAGES:
        return False, f"Unsupported language '{language}'. Allowed: {sorted(ALLOWED_LANGUAGES)}"
    return True, ""


def get_display_name(language: str) -> str:
    cfg = get_language_config(language)
    return cfg["display_name"] if cfg else language

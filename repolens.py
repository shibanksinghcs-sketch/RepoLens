
#!/usr/bin/env python3
"""
RepoLens
Graphify-guided Python test generation using Gemma,
pytest execution, mutation verification, and JSON reporting.

Python 3.10+
Install: python -m pip install pytest

IMPORTANT:
- Only use on repositories you trust.
- Generated tests and repository code are executed locally.
- AST screening is not a security sandbox.
"""
import textwrap
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    "__pycache__", "build", "dist", ".tox",
    "site-packages", ".repolens_cache", "repolens_out",
}

DEFAULT_MODEL = "gemma-4-26b-a4b-it"


# ---------------------------------------------------------
# 1. SCAN PYTHON SOURCE CODE
# ---------------------------------------------------------

def python_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if filename.endswith(".py"):
                yield Path(root) / filename


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def calculate_complexity(node):
    complexity = 1

    for item in ast.walk(node):
        if isinstance(
            item,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.ExceptHandler,
                ast.IfExp,
            ),
        ):
            complexity += 1

        elif isinstance(item, ast.BoolOp):
            complexity += max(0, len(item.values) - 1)

        elif isinstance(item, ast.comprehension):
            complexity += 1

    return complexity


def scan_functions(repo):
    functions = []

    for path in python_files(repo):
        try:
            source = read_text(path)
            tree = ast.parse(source)
        except (SyntaxError, OSError) as exc:
            print(f"[WARNING] Skipping {path}: {exc}")
            continue

        lines = source.splitlines()
        relative = path.relative_to(repo).as_posix()

        relative_lower = relative.lower()
        if (
            "/tests/" in "/" + relative_lower
            or path.name.lower().startswith("test_")
            or path.name.lower() == "conftest.py"
            ):
            continue
        module = relative[:-3].replace("/", ".")


        if module.endswith(".__init__"):
            module = module[:-9]

        for node in tree.body:
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue

            start = min(
                [node.lineno]
                + [decorator.lineno for decorator in node.decorator_list]
            )
            end = getattr(node, "end_lineno", node.lineno)

            arguments = [
                arg.arg
                for arg in node.args.posonlyargs + node.args.args
            ]

            if node.args.vararg:
                arguments.append("*" + node.args.vararg.arg)

            arguments.extend(
                arg.arg for arg in node.args.kwonlyargs
            )

            if node.args.kwarg:
                arguments.append("**" + node.args.kwarg.arg)

            functions.append({
                "name": node.name,
                "module": module,
                "qualname": f"{module}::{node.name}",
                "file": relative,
                "lineno": start,
                "end_lineno": end,
                "args": arguments,
                "source": "\n".join(lines[start - 1:end]),
                "docstring": ast.get_docstring(node) or "",
                "complexity": calculate_complexity(node),
                "dependents": 0,
                "tested_name_heuristic": False,
                "score": 0.0,
            })

    return functions


# ---------------------------------------------------------
# 2. GRAPHIFY DEPENDENCY GRAPH
# ---------------------------------------------------------

def graph_node_name(value):
    if isinstance(value, dict):
        for key in (
            "qualified_name", "qualifiedName",
            "name", "label", "symbol", "title"
        ):
            if value.get(key) is not None:
                return str(value[key])

    return str(value) if value is not None else ""


def normalize_function_name(value):
    value = value.replace("\\", "/")

    if "::" in value:
        value = value.rsplit("::", 1)[-1]

    value = re.sub(r"\(.*$", "", value)
    return value.rsplit(".", 1)[-1].strip()


def load_graphify_dependents(graph_path, functions):
    if not graph_path or not graph_path.is_file():
        return {}

    try:
        graph = json.loads(read_text(graph_path))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARNING] Cannot read Graphify graph: {exc}")
        return {}

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", graph.get("links", []))

    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {}

    node_names = {}

    for node in nodes:
        if not isinstance(node, dict):
            continue

        node_id = node.get("id", node.get("key"))

        if node_id is not None:
            node_names[str(node_id)] = graph_node_name(node)

    counts = {function["name"]: 0 for function in functions}
    matched = False

    for edge in edges:
        if not isinstance(edge, dict):
            continue

        source = edge.get("source", edge.get("from", edge.get("src")))
        target = edge.get("target", edge.get("to", edge.get("dst")))

        if target is None:
            continue

        target_name = normalize_function_name(
            node_names.get(str(target), str(target))
        )

        for function in functions:
            if target_name == function["name"]:
                counts[function["name"]] += 1
                matched = True

    return counts if matched else {}


def find_test_name_mentions(repo, functions):
    """
    Heuristic only. This is NOT actual test coverage measurement.
    """
    mentioned = set()

    for path in python_files(repo):
        relative = "/" + path.relative_to(repo).as_posix().lower()

        if "test" not in path.name.lower() and "/tests/" not in relative:
            continue

        try:
            source = read_text(path)
        except OSError:
            continue

        for function in functions:
            if re.search(
                rf"\b{re.escape(function['name'])}\b", source
            ):
                mentioned.add(function["name"])

    return mentioned


def rank_functions(repo, functions, graph_path=None):
    dependencies = load_graphify_dependents(graph_path, functions)
    mentions = find_test_name_mentions(repo, functions)

    source = "Graphify" if dependencies else "static fallback"

    for function in functions:
        function["tested_name_heuristic"] = (
            function["name"] in mentions
        )

        if dependencies:
            function["dependents"] = dependencies.get(
                function["name"], 0
            )
        else:
            # Approximation: references in other Python files.
            count = 0

            for path in python_files(repo):
                if path.relative_to(repo).as_posix() == function["file"]:
                    continue

                try:
                    count += len(
                        re.findall(
                            rf"\b{re.escape(function['name'])}\b",
                            read_text(path),
                        )
                    )
                except OSError:
                    pass

            function["dependents"] = count

        # Prioritization heuristic, NOT a probability.
        function["score"] = (
            0.35
            + min(function["dependents"], 10) * 0.09
            + min(max(function["complexity"] - 1, 0), 10) * 0.035
            + (
                0.12
                if not function["tested_name_heuristic"]
                else 0
            )
            + (0.025 if function["docstring"] else 0)
        )

    functions.sort(key=lambda item: item["score"], reverse=True)
    return functions, source


# ---------------------------------------------------------
# 3. GEMMA API
# ---------------------------------------------------------


def post_json(url, payload, headers=None, timeout=180):
    """POST JSON with retries for temporary API/server failures."""
    import time

    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    retryable_statuses = {429, 500, 502, 503, 504}
    max_attempts = 3

    for attempt in range(max_attempts):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=request_headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=timeout
            ) as response:
                body = response.read().decode(
                    "utf-8", errors="replace"
                )
            break

        except urllib.error.HTTPError as exc:
            details = exc.read().decode(
                "utf-8", errors="replace"
            )

            if (
                exc.code in retryable_statuses
                and attempt < max_attempts - 1
            ):
                delay = 2 ** (attempt + 1)
                print(
                    f"[WARN] API HTTP {exc.code}; "
                    f"retrying in {delay}s "
                    f"({attempt + 2}/{max_attempts})..."
                )
                time.sleep(delay)
                continue

            raise RuntimeError(
                f"Model API HTTP {exc.code}: {details[:2000]}"
            ) from exc

        except urllib.error.URLError as exc:
            if attempt < max_attempts - 1:
                delay = 2 ** (attempt + 1)
                print(
                    f"[WARN] API connection failed; "
                    f"retrying in {delay}s..."
                )
                time.sleep(delay)
                continue

            raise RuntimeError(
                f"Cannot reach model API: {exc}"
            ) from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid API response: {body[:1000]}"
        ) from exc

def call_gemma(prompt):
    backend = os.environ.get("GEMMA_BACKEND", "gemini").lower()
    model = os.environ.get("GEMMA_MODEL", DEFAULT_MODEL)

    cache_enabled = os.environ.get("REPOLENS_CACHE", "1") != "0"

    cache_key = hashlib.sha256(
        f"{backend}|{model}|{prompt}".encode()
    ).hexdigest()[:24]

    cache_path = Path(".repolens_cache") / f"{cache_key}.txt"

    if cache_enabled and cache_path.exists():
        print("[INFO] Using cached model response.")
        return read_text(cache_path)

    if backend == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Set it in PowerShell."
            )

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )

        result = post_json(
            url,
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 4096,
                },
            },
            headers={"x-goog-api-key": api_key},
        )

        try:
            output = "".join(
                part.get("text", "")
                for part in result["candidates"][0]["content"]["parts"]
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected Gemma response: {json.dumps(result)[:2000]}"
            ) from exc

    elif backend == "ollama":
        model = os.environ.get("GEMMA_MODEL")

        if not model:
            raise RuntimeError("Set GEMMA_MODEL to your Ollama model name.")

        url = (
            os.environ.get(
                "OLLAMA_URL", "http://localhost:11434"
            ).rstrip("/")
            + "/api/generate"
        )

        result = post_json(
            url,
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )

        output = result.get("response", "")

    elif backend == "mock":
        mock_file = os.environ.get("REPOLENS_MOCK_FILE")

        if not mock_file:
            raise RuntimeError("Set REPOLENS_MOCK_FILE to a test response file.")

        output = read_text(Path(mock_file))

    else:
        raise RuntimeError(
            f"Unsupported GEMMA_BACKEND={backend!r}. "
            "Use gemini, ollama, or mock."
        )

    output = output[:40000]

    if cache_enabled:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(output, encoding="utf-8")

    return output


# ---------------------------------------------------------
# 4. BUILD THE TEST GENERATION PROMPT
# ---------------------------------------------------------

def build_prompt(target):
    return f"""
You are a senior Python testing engineer.

Generate pytest tests for this target function.

Module to import: {target['module']}
Function: {target['name']}
Arguments: {target['args']}
File: {target['file']}
Docstring: {target['docstring'] or "(none)"}

Source code:
```python
{target['source']}
```

Requirements:
1. Return exactly one Python fenced code block.
2. Import the real function from the module shown above.
3. Generate at most five deterministic pytest tests.
4. Test normal cases, boundary values and meaningful edge cases.
5. Test exceptions only when justified by the implementation.
6. Do not change the original implementation.
7. Do not use network, filesystem, subprocess, shell commands,
   eval, exec, reflection tricks, or random values.
8. Avoid unsupported assumptions.
9. Tests must genuinely call the target function.
""".strip()


def extract_test_code(response):
    match = re.search(
        r"```(?:python|py)?[ \t]*\n(.*?)```",
        response,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            "Gemma did not return a Python fenced code block."
        )

    code = textwrap.dedent(match.group(1)).strip()

    if not code:
        raise RuntimeError("Gemma returned an empty test block.")

    return code + "\n"



# ---------------------------------------------------------
# 5. BASIC GENERATED-CODE SCREENING
# ---------------------------------------------------------

def safety_check(code, module):
    """
    Conservative AST screening, NOT a security sandbox.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    allowed_imports = {
        "pytest", "math", "re", "datetime", "statistics",
        module.split(".")[0],
    }

    forbidden_calls = {
        "eval", "exec", "compile", "__import__", "open",
        "input", "breakpoint", "globals", "locals", "vars",
        "setattr", "delattr", "system", "popen", "run",
        "Popen", "call", "check_call", "check_output",
        "urlopen", "socket",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed_imports:
                    return False, f"Disallowed import: {alias.name}"

        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]

            if root not in allowed_imports:
                return False, f"Disallowed import: {node.module}"

        elif isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in forbidden_calls
            ):
                return False, f"Disallowed call: {node.func.id}"

            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in forbidden_calls
            ):
                return False, f"Disallowed call: {node.func.attr}"

    return True, "Basic AST screening passed; this is not a sandbox."


# ---------------------------------------------------------
# 6. TEST EXECUTION IN TEMPORARY COPIES
# ---------------------------------------------------------

def copy_repository(repo, destination):
    shutil.copytree(
        repo,
        destination,
        ignore=shutil.ignore_patterns(
            *SKIP_DIRS, "*.pyc", ".DS_Store"
        ),
    )


def run_command(command, cwd, timeout=30, env=None):
    environment = os.environ.copy()

    if env:
        environment.update(env)

    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    return subprocess.run(
        command,
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def check_import(repo, target):
    """
    Importing a repository module executes its top-level code.
    Only do this for trusted repositories.
    """
    with tempfile.TemporaryDirectory(prefix="repolens-import-") as temp:
        copy_path = Path(temp) / "repo"
        copy_repository(repo, copy_path)

        script = (
            "import importlib\n"
            f"module = importlib.import_module({target['module']!r})\n"
            f"assert hasattr(module, {target['name']!r})\n"
        )

        try:
            result = run_command(
                [sys.executable, "-c", script],
                copy_path,
                timeout=15,
                env={"PYTHONPATH": str(copy_path)},
            )
        except subprocess.TimeoutExpired:
            return False, "Import timed out."

        output = (result.stdout + "\n" + result.stderr).strip()

        return (
            result.returncode == 0,
            output or "Import succeeded.",
        )


def run_pytest(repo, target, test_code, timeout=30):
    with tempfile.TemporaryDirectory(prefix="repolens-tests-") as temp:
        copy_path = Path(temp) / "repo"
        copy_repository(repo, copy_path)

        tests_dir = copy_path / "tests"
        tests_dir.mkdir(exist_ok=True)

        test_file = tests_dir / "test_repolens_generated.py"
        test_file.write_text(test_code, encoding="utf-8")

        try:
            result = run_command(
                [
                    sys.executable, "-m", "pytest",
                    "-q", "tests/test_repolens_generated.py",
                ],
                copy_path,
                timeout=timeout,
                env={"PYTHONPATH": str(copy_path)},
            )
        except subprocess.TimeoutExpired:
            return 124, "Pytest timed out."

        return (
            result.returncode,
            (result.stdout + "\n" + result.stderr).strip()[-12000:],
        )


# ---------------------------------------------------------
# 7. MUTATION VERIFICATION
# ---------------------------------------------------------

def replace_function_with_stub(repo_copy, target):
    path = repo_copy / target["file"]

    source = read_text(path)
    tree = ast.parse(source, filename=str(path))
    lines = source.splitlines(keepends=True)

    target_node = None

    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == target["name"]
        ):
            target_node = node
            break

    if target_node is None:
        raise RuntimeError("Could not find function to mutate.")

    start = min(
        [target_node.lineno]
        + [d.lineno for d in target_node.decorator_list]
    )
    end = getattr(target_node, "end_lineno", target_node.lineno)

    # Basic mutation: destroy the original return behaviour.
    stub = (
        f"def {target['name']}(*args, **kwargs):\n"
        "    return None\n"
    )

    lines[start - 1:end] = [stub]
    path.write_text("".join(lines), encoding="utf-8")


def mutation_check(repo, target, test_code, timeout=30):
    with tempfile.TemporaryDirectory(prefix="repolens-mutant-") as temp:
        copy_path = Path(temp) / "repo"
        copy_repository(repo, copy_path)

        try:
            replace_function_with_stub(copy_path, target)
        except (OSError, SyntaxError, RuntimeError) as exc:
            return False, f"Mutation setup failed: {exc}"

        tests_dir = copy_path / "tests"
        tests_dir.mkdir(exist_ok=True)

        test_file = tests_dir / "test_repolens_generated.py"
        test_file.write_text(test_code, encoding="utf-8")

        try:
            result = run_command(
                [
                    sys.executable, "-m", "pytest",
                    "-q", "tests/test_repolens_generated.py",
                ],
                copy_path,
                timeout=timeout,
                env={"PYTHONPATH": str(copy_path)},
            )
        except subprocess.TimeoutExpired:
            return False, "Mutation test timed out; not counted as detected."

        output = (result.stdout + "\n" + result.stderr).strip()[-12000:]

        # Mutation is detected when the tests fail on the broken function.
        return result.returncode != 0, output


# ---------------------------------------------------------
# 8. REPORT AND PATCH OUTPUT
# ---------------------------------------------------------

def write_report(
    output_dir,
    target,
    dependency_source,
    test_code,
    original_output,
    mutation_output,
    passed_original,
    mutation_detected,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    status = (
        "VERIFIED"
        if passed_original and mutation_detected
        else "FAILED_ORIGINAL_TESTS"
        if not passed_original
        else "MUTATION_NOT_DETECTED"
    )

    report = {
        "tool": "RepoLens",
        "target": target,
        "dependency_source": dependency_source,
        "test_mention_note": (
            "Test-name matching is a heuristic, not actual code coverage."
        ),
        "generated_tests_pass_original": passed_original,
        "generated_tests_detect_mutation": mutation_detected,
        "status": status,
        "original_test_output": original_output,
        "mutation_test_output": mutation_output,
    }

    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    (output_dir / "test_repolens_generated.py").write_text(
        test_code, encoding="utf-8"
    )

    patch_lines = [
        "*** Begin Patch",
        "*** Add File: tests/test_repolens_generated.py",
    ]

    patch_lines.extend(
        "+" + line for line in test_code.rstrip("\n").splitlines()
    )
    patch_lines.append("*** End Patch")

    (output_dir / "tests.patch").write_text(
        "\n".join(patch_lines) + "\n",
        encoding="utf-8",
    )

    return status


# ---------------------------------------------------------
# 9. MAIN WORKFLOW
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "RepoLens: Graphify-guided test generation "
            "and mutation verification using Gemma."
        )
    )

    parser.add_argument("repo", help="Target Python repository directory")
    parser.add_argument("--graph", help="Path to Graphify graph.json")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--pick", type=int, default=0)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--out", default="repolens_out")

    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()

    if not repo.is_dir():
        print(f"ERROR: Repository not found: {repo}")
        return 2

    graph_path = (
        Path(args.graph).expanduser().resolve()
        if args.graph else None
    )

    if graph_path and not graph_path.is_file():
        print("[WARNING] Graphify graph not found; using static fallback.")
        graph_path = None

    functions = scan_functions(repo)

    if not functions:
        print("No top-level Python functions found.")
        return 1

    functions, dependency_source = rank_functions(
        repo, functions, graph_path
    )

    print(
        f"Scanned {len(functions)} functions; "
        f"dependency source: {dependency_source}"
    )
    print()
    print(
        f"{'#':<4}{'Score':<9}{'Deps':<7}"
        f"{'Test*':<8}{'Doc':<6}{'Cx':<5}Function"
    )

    for index, function in enumerate(functions[:max(1, args.top)]):
        print(
            f"{index:<4}"
            f"{function['score']:<9.2f}"
            f"{function['dependents']:<7}"
            f"{('yes' if function['tested_name_heuristic'] else 'no'):<8}"
            f"{('yes' if function['docstring'] else 'no'):<6}"
            f"{function['complexity']:<5}"
            f"{function['qualname']}"
        )

    print("\n* Test* is a name-mention heuristic, NOT test coverage.")

    if args.no_llm:
        return 0

    if args.pick < 0 or args.pick >= len(functions):
        print(f"ERROR: --pick must be 0 to {len(functions) - 1}.")
        return 2

    target = functions[args.pick]

    print(f"\n[1/5] Selected: {target['qualname']}")

    print("[2/5] Checking module import...")
    import_ok, import_output = check_import(repo, target)

    if not import_ok:
        print("Import check failed:")
        print(import_output)
        return 1

    print("Import check passed.")

    print("[3/5] Generating tests with Gemma...")

    try:
        response = call_gemma(build_prompt(target))
        test_code = extract_test_code(response)
    except Exception as exc:
        print(f"Generation failed: {exc}")
        return 1

    safe, message = safety_check(test_code, target["module"])
    print(message)

    if not safe:
        print("Refusing to execute generated tests.")
        return 1

    print("[4/5] Running tests against original function...")

    original_rc, original_output = run_pytest(
        repo, target, test_code, args.timeout
    )

    print(original_output or "(No test output)")
    passed_original = original_rc == 0

    if not passed_original:
        print("\nTests failed on original implementation.")
        status = write_report(
            Path(args.out), target, dependency_source,
            test_code, original_output, "",
            False, False,
        )
        print(f"Status: {status}")
        print(f"Report: {Path(args.out).resolve() / 'report.json'}")
        return 1

    print("[5/5] Testing against a deliberately broken function...")

    mutation_detected, mutation_output = mutation_check(
        repo, target, test_code, args.timeout
    )

    print(mutation_output or "(No mutation test output)")

    status = write_report(
        Path(args.out),
        target,
        dependency_source,
        test_code,
        original_output,
        mutation_output,
        passed_original,
        mutation_detected,
    )

    output_dir = Path(args.out).resolve()

    print(f"\nStatus: {status}")
    print(f"Report: {output_dir / 'report.json'}")
    print(f"Tests:  {output_dir / 'test_repolens_generated.py'}")
    print(f"Patch:  {output_dir / 'tests.patch'}")

    if mutation_detected:
        print(
            "\nSUCCESS: Tests passed on the original implementation "
            "and detected the deliberately broken version."
        )
        print(
            "Note: this verifies one simple mutation, "
            "not a comprehensive mutation-testing score."
        )
        return 0

    print(
        "\nThe tests passed originally but did not detect the mutation. "
        "Review the generated tests."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

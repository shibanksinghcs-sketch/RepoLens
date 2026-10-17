from __future__ import annotations

import ast
import html
import json
import os
import queue
import re
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import streamlit as st


# ── Configuration ──────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
ENGINE = BASE_DIR / "repolens.py"
DEFAULT_REPO = BASE_DIR / "demo-repo"
OUTPUT_DIR = BASE_DIR / "repolens_out"

REPORT_FILE = OUTPUT_DIR / "report.json"
TEST_FILE = OUTPUT_DIR / "test_repolens_generated.py"
PATCH_FILE = OUTPUT_DIR / "tests.patch"

STAGE_RE = re.compile(r"^\s*\[(\d+)\s*/\s*(\d+)\]\s*(.*)$")
IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", ".mypy_cache", ".pytest_cache",
}

st.set_page_config(
    page_title="RepoLens — Code Intelligence",
    page_icon="⌘",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styling (no external fonts: works offline) ──────────────────

st.markdown(
    """
    <style>
    :root {
        --bg: #101114; --panel: #17181d; --panel2: #1d1e25; --border: #2a2b35;
        --text: #efeff5; --muted: #9293a4; --violet: #a78bfa;
        --green: #65d6a0; --red: #ff7d91; --amber: #f4c77b;
        --sans: Inter, "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
        --mono: "DM Mono", "Cascadia Mono", Consolas, "SFMono-Regular", Menlo, monospace;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg); color: var(--text); font-family: var(--sans);
    }
    [data-testid="stHeader"] { background: rgba(16,17,20,.88); border-bottom: 1px solid var(--border); }
    [data-testid="stSidebar"] { background: #141519; border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1600px; }
    h1, h2, h3, p, label { color: var(--text); }
    h1 { font-size: 1.75rem !important; letter-spacing: -0.055em !important; font-weight: 800 !important; }
    h2 { font-size: 1.15rem !important; letter-spacing: -0.025em !important; }
    h3 { font-size: .98rem !important; }
    [data-testid="stCaptionContainer"], .muted { color: var(--muted) !important; }
    code, pre, [data-testid="stCode"] { font-family: var(--mono) !important; }

    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] > div > div, [data-testid="stTextArea"] textarea {
        background: #111216 !important; color: var(--text) !important;
        border-color: var(--border) !important; border-radius: 8px !important;
    }
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
        border-radius: 8px; min-height: 2.55rem; font-weight: 600;
        transition: border-color .15s ease, transform .15s ease;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: var(--violet); color: #17121f; border: 1px solid var(--violet);
    }
    [data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover {
        border-color: var(--violet); transform: translateY(-1px);
    }
    [data-testid="stMetric"] {
        background: var(--panel); border: 1px solid var(--border);
        padding: 15px 17px; border-radius: 11px;
    }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: .78rem !important; }
    [data-testid="stMetricValue"] { color: var(--text) !important; font-size: 1.55rem !important; font-weight: 750 !important; }
    [data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 10px; background: var(--panel); }
    [data-testid="stAlert"] { border-radius: 10px; }
    hr { border-color: var(--border) !important; }

    .brand { display: flex; align-items: center; gap: 10px; margin: 0 0 24px 0; }
    .brand-mark {
        display: flex; align-items: center; justify-content: center; width: 37px; height: 37px;
        border: 1px solid #51417b; background: #282138; color: #c4b5fd;
        border-radius: 10px; font-size: 20px; font-weight: 800;
    }
    .brand-name { font-size: 1.15rem; font-weight: 800; letter-spacing: -.04em; color: #f3f0ff; }
    .brand-sub { color: var(--muted); font-size: .7rem; margin-top: 1px; }
    .eyebrow {
        color: var(--violet); font-family: var(--mono); text-transform: uppercase;
        letter-spacing: .12em; font-size: .7rem; font-weight: 500;
    }
    .hero-title {
        font-size: clamp(1.65rem, 3vw, 2.4rem); line-height: 1.14; letter-spacing: -.06em;
        font-weight: 800; margin: 8px 0; color: #f5f3ff;
    }
    .hero-copy { color: #a3a3b4; font-size: .93rem; line-height: 1.65; max-width: 650px; margin-bottom: 20px; }
    .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 17px; margin-bottom: 14px; }
    .panel-heading { font-size: .9rem; font-weight: 700; color: #f1eff8; margin-bottom: 5px; }
    .panel-sub { color: var(--muted); font-size: .78rem; line-height: 1.5; }
    .file-row {
        display: flex; align-items: center; gap: 8px; padding: 6px 8px; margin: 2px 0;
        color: #c4c4d1; font-family: var(--mono); font-size: .76rem; border-radius: 6px; overflow-wrap: anywhere;
    }
    .file-icon { color: #a78bfa; flex-shrink: 0; }
    .status-pill {
        display: inline-block; padding: 4px 9px; border-radius: 6px; font-family: var(--mono);
        font-size: .72rem; font-weight: 500; border: 1px solid var(--border);
        background: #202128; color: #c9c9d6;
    }
    .status-good { color: var(--green); border-color: #285c48; background: #142820; }
    .status-bad  { color: var(--red);   border-color: #683541; background: #2b171d; }
    .status-warn { color: var(--amber); border-color: #69522c; background: #292216; }
    .section-label {
        font-family: var(--mono); color: var(--muted); text-transform: uppercase;
        font-size: .68rem; letter-spacing: .1em; margin: 12px 0 8px;
    }

    /* Pipeline strip */
    .pipe { display: flex; gap: 8px; margin: 14px 0 6px; flex-wrap: wrap; }
    .stage {
        flex: 1 1 120px; min-width: 120px; background: var(--panel); border: 1px solid var(--border);
        border-radius: 10px; padding: 10px 12px;
    }
    .stage-n { font-family: var(--mono); font-size: .66rem; letter-spacing: .1em; color: var(--muted); }
    .stage-msg { font-size: .76rem; color: #d6d6e2; margin: 5px 0 7px; line-height: 1.35; min-height: 2.1em; overflow-wrap: anywhere; }
    .stage-state { font-family: var(--mono); font-size: .66rem; text-transform: uppercase; letter-spacing: .08em; }
    .stage.pending .stage-state { color: var(--muted); }
    .stage.running { border-color: #51417b; background: #1d1a28; }
    .stage.running .stage-state { color: var(--violet); }
    .stage.done { border-color: #285c48; }
    .stage.done .stage-state { color: var(--green); }
    .stage.failed { border-color: #683541; background: #231418; }
    .stage.failed .stage-state { color: var(--red); }

    /* Evidence card */
    .evidence { border: 1px solid var(--border); border-radius: 14px; padding: 20px 22px; background: var(--panel); margin: 10px 0 16px; }
    .evidence.good { border-color: #285c48; background: linear-gradient(180deg, #14211b, var(--panel)); }
    .evidence.bad  { border-color: #683541; background: linear-gradient(180deg, #25151a, var(--panel)); }
    .evidence.warn { border-color: #69522c; background: linear-gradient(180deg, #241e13, var(--panel)); }
    .ev-badge { font-size: 1.7rem; font-weight: 800; letter-spacing: -.04em; margin-bottom: 12px; }
    .evidence.good .ev-badge { color: var(--green); }
    .evidence.bad .ev-badge  { color: var(--red); }
    .evidence.warn .ev-badge { color: var(--amber); }
    .ev-row { display: flex; align-items: center; gap: 10px; padding: 5px 0; font-size: .88rem; color: #e2e2ec; }
    .ev-ic { font-weight: 800; width: 1.2rem; text-align: center; }
    .ev-ic.ok { color: var(--green); } .ev-ic.no { color: var(--red); } .ev-ic.na { color: var(--amber); }
    .ev-foot { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }

    @media (max-width: 850px) {
        .block-container { padding: 1rem .85rem 2rem; }
        .hero-title { font-size: 1.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────

def esc(value) -> str:
    return html.escape(str(value), quote=True)


def resolve_path(raw_path: str) -> Path:
    """Resolve absolute paths or paths relative to the app directory."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def discover_python_files(repo: Path) -> list[Path]:
    found = []
    try:
        for path in sorted(repo.rglob("*.py")):
            if any(part in IGNORED_DIRS for part in path.relative_to(repo).parts):
                continue
            found.append(path)
    except OSError:
        pass
    return found


def discover_top_level_functions(repo: Path) -> list[dict]:
    """AST preview only. The engine's own candidate ordering is authoritative."""
    candidates = []
    for path in discover_python_files(repo):
        lower_parts = [p.lower() for p in path.relative_to(repo).parts]
        if "tests" in lower_parts or "test" in lower_parts:
            continue
        if path.name.lower().startswith("test_") or path.name.lower() == "conftest.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidates.append({
                    "name": node.name,
                    "file": path.relative_to(repo).as_posix(),
                    "line": node.lineno,
                })
    return candidates


def safe_read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def read_report() -> dict | None:
    if not REPORT_FILE.is_file():
        return None
    try:
        with REPORT_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def report_is_fresh(run_data: dict | None) -> bool:
    """A report only counts if it was written by the run made in this session."""
    if not run_data or not REPORT_FILE.is_file():
        return False
    try:
        return REPORT_FILE.stat().st_mtime >= run_data["started_at"] - 1
    except OSError:
        return False


def clear_previous_outputs() -> None:
    for path in (REPORT_FILE, TEST_FILE, PATCH_FILE):
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def short_name(target: dict) -> str:
    name = target.get("qualname") or target.get("name") or ""
    return re.split(r"[:.]+", str(name))[-1] if name else ""


def mutation_preview(source: str) -> str | None:
    """Show what the engine's mutation (body replaced by `return None`) looks like."""
    try:
        tree = ast.parse(textwrap.dedent(source))
        node = tree.body[0]
        if not isinstance(node, ast.FunctionDef):
            return None
        return f"def {node.name}({ast.unparse(node.args)}):\n    return None\n"
    except (SyntaxError, IndexError, ValueError):
        return None


def detect_generation_source(report: dict, lines: list[str]) -> str | None:
    """Returns 'live', 'cached' or None. Never guesses 'live' without a signal."""
    for key in ("cached", "from_cache", "cache_hit", "used_cache", "response_cached"):
        if key in report and isinstance(report[key], bool):
            return "cached" if report[key] else "live"
    for key in ("response_source", "generation_source", "source"):
        val = report.get(key)
        if isinstance(val, str):
            low = val.lower()
            if "cache" in low or "replay" in low:
                return "cached"
            if "live" in low or "api" in low:
                return "live"
    text = "\n".join(lines).lower()
    if any(p in text for p in ("cache hit", "cached response", "using cache", "from cache", "replay")):
        return "cached"
    return None


def first_present(report: dict, keys: tuple[str, ...]):
    for key in keys:
        if key in report and report[key] not in (None, ""):
            return report[key]
    return None


def ranking_rows(report: dict) -> list[dict] | None:
    for key in ("candidates", "ranking", "ranked", "top_candidates"):
        val = report.get(key)
        if isinstance(val, list) and val and all(isinstance(v, dict) for v in val):
            rows = []
            for item in val:
                rows.append({
                    k: v for k, v in item.items()
                    if isinstance(v, (int, float, bool)) or (isinstance(v, str) and len(v) <= 80)
                })
            return rows
    return None


# ── Pipeline strip ─────────────────────────────────────────────

def parse_stages(lines: list[str]) -> tuple[dict[int, str], int]:
    stages: dict[int, str] = {}
    total = 5
    for line in lines:
        m = STAGE_RE.match(line)
        if m:
            stages[int(m.group(1))] = m.group(3).strip()
            total = int(m.group(2))
    return stages, total


def pipeline_html(lines: list[str], state: str) -> str:
    """state: running | done | failed. Stage text comes from the engine's own [n/N] lines."""
    stages, total = parse_stages(lines)
    last = max(stages) if stages else 0
    boxes = []
    for n in range(1, total + 1):
        msg = stages.get(n)
        if msg is None:
            cls, label, text = "pending", "pending", "—"
        else:
            text = msg[:70]
            if n < last:
                cls, label = "done", "done"
            else:
                cls, label = state, {"running": "running", "done": "done", "failed": "failed"}[state]
        boxes.append(
            f'<div class="stage {cls}"><div class="stage-n">STEP {n}/{total}</div>'
            f'<div class="stage-msg">{esc(text)}</div>'
            f'<div class="stage-state">{label}</div></div>'
        )
    return '<div class="pipe">' + "".join(boxes) + "</div>"


def run_engine(command: list[str], total_timeout: int, on_line) -> tuple[list[str], int, float, bool]:
    """Stream the engine's output line by line so the UI can update while it runs."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    start = time.time()
    proc = subprocess.Popen(
        command, cwd=str(BASE_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", env=env, bufsize=1,
    )
    q: queue.Queue = queue.Queue()

    def reader() -> None:
        for line in proc.stdout:  # type: ignore[union-attr]
            q.put(line)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    lines: list[str] = []
    timed_out = False
    finished = False
    while not finished:
        try:
            item = q.get(timeout=0.25)
            if item is None:
                finished = True
            else:
                lines.append(item.rstrip("\r\n"))
                on_line(lines)
        except queue.Empty:
            pass
        if time.time() - start > total_timeout:
            timed_out = True
            proc.kill()
            break
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    return lines, (proc.returncode if proc.returncode is not None else -1), time.time() - start, timed_out


# ── Sidebar ────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">⌘</div>
            <div>
                <div class="brand-name">RepoLens</div>
                <div class="brand-sub">CODE INTELLIGENCE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
    repo_input = st.text_input(
        "Repository path",
        value=str(DEFAULT_REPO),
        help="Absolute path, or a path relative to the RepoLens folder.",
    )
    repo_path = resolve_path(repo_input)

    st.markdown('<div class="section-label">Repository explorer</div>', unsafe_allow_html=True)
    if repo_path.is_dir():
        files = discover_python_files(repo_path)
        if files:
            for path in files[:80]:
                relative = path.relative_to(repo_path).as_posix()
                st.markdown(
                    f'<div class="file-row"><span class="file-icon">PY</span>'
                    f'<span>{esc(relative)}</span></div>',
                    unsafe_allow_html=True,
                )
            if len(files) > 80:
                st.caption(f"+ {len(files) - 80} more Python files")
            st.caption(f"{len(files)} Python files found")
        else:
            st.caption("No Python files found in this repository.")
    else:
        st.warning("Repository folder not found.")

    st.divider()
    st.markdown('<div class="eyebrow">Analysis settings</div>', unsafe_allow_html=True)

    graph_input = st.text_input(
        "Graphify graph path (optional)",
        value="",
        placeholder=r"C:\path\to\graph.json",
        help="Leave blank to let RepoLens use its fallback behavior.",
    )
    timeout = st.slider(
        "Per-command timeout", min_value=10, max_value=120, value=30, step=5,
        help="RepoLens may run multiple commands, so total run time can be longer.",
    )
    heuristic_only = st.toggle(
        "Heuristic-only mode", value=False,
        help="Passes --no-llm to RepoLens. Generated AI tests may not be available.",
    )

    st.divider()
    st.markdown(
        '<div class="panel-sub">Local-first interface · Runs your existing RepoLens engine</div>',
        unsafe_allow_html=True,
    )


# ── Main workspace ─────────────────────────────────────────────

left, right = st.columns([0.39, 0.61], gap="large")

with left:
    st.markdown('<div class="eyebrow">Repository overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Understand your code.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-copy">Find important functions, generate focused tests, '
        'and check whether those tests catch a deliberate code mutation.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="panel-heading">01 / Target selection</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-sub">Choose the candidate index passed to the engine '
        'using <code>--pick</code>.</div>',
        unsafe_allow_html=True,
    )

    candidates = discover_top_level_functions(repo_path) if repo_path.is_dir() else []
    preview_name = ""

    if candidates:
        labels = [
            f"{i}  ·  {c['name']}  —  {c['file']}:{c['line']}" for i, c in enumerate(candidates)
        ]
        selected_label = st.selectbox(
            "Preview candidates",
            options=labels,
            index=0,
            help="AST-based preview. The engine's own ranking is authoritative; "
                 "the report below shows which function it really chose.",
        )
        pick = labels.index(selected_label)
        chosen = candidates[pick]
        preview_name = chosen["name"]
        st.markdown(
            f"""
            <div class="panel">
                <div class="eyebrow">Selected preview</div>
                <div style="font-family:var(--mono);font-size:1.05rem;font-weight:500;
                            margin:9px 0;color:#ddd6fe;">{esc(chosen["name"])}</div>
                <div class="panel-sub">{esc(chosen["file"])} · line {chosen["line"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        pick = st.number_input("Function index (--pick)", min_value=0, value=0, step=1)
        st.caption("No function preview is available. The engine will validate the index.")

    st.markdown('<div class="section-label">Before you run</div>', unsafe_allow_html=True)
    checks = [
        ("Engine", ENGINE.is_file()),
        ("Repository", repo_path.is_dir()),
        ("Python files", bool(discover_python_files(repo_path)) if repo_path.is_dir() else False),
        ("API key in this terminal", bool(os.environ.get("GEMINI_API_KEY"))),
    ]
    for label, passed in checks:
        color = "#65d6a0" if passed else "#f4c77b"
        st.markdown(
            f'<div class="file-row"><span style="color:{color};font-weight:800;">'
            f'{"✓" if passed else "!"}</span><span>{label}</span></div>',
            unsafe_allow_html=True,
        )
    if not os.environ.get("GEMINI_API_KEY"):
        st.caption("No key is visible to this process. Live generation will fail; "
                   "a cached run can still work.")

    st.markdown("")
    analyze_clicked = st.button(
        "▶  Analyze repository",
        type="primary",
        use_container_width=True,
        disabled=not ENGINE.is_file() or not repo_path.is_dir(),
    )

with right:
    st.markdown('<div class="eyebrow">Analysis console</div>', unsafe_allow_html=True)
    st.markdown("## Test generation & verification")
    st.markdown(
        '<div class="panel-sub">Run the engine, watch each stage, inspect the evidence, '
        'and download the generated artifacts.</div>',
        unsafe_allow_html=True,
    )

    pipeline_slot = st.empty()
    live_slot = st.empty()

    if analyze_clicked:
        graph_path = None
        if graph_input.strip():
            graph_path = resolve_path(graph_input)
            if not graph_path.is_file():
                st.error(f"Graph file not found: {graph_path}")
                st.stop()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        clear_previous_outputs()

        command = [
            sys.executable, "-u", str(ENGINE), str(repo_path),
            "--pick", str(int(pick)),
            "--timeout", str(int(timeout)),
            "--out", str(OUTPUT_DIR),
        ]
        if graph_path is not None:
            command.extend(["--graph", str(graph_path)])
        if heuristic_only:
            command.append("--no-llm")

        started_at = time.time()
        pipeline_slot.markdown(pipeline_html([], "running"), unsafe_allow_html=True)

        def on_line(lines: list[str]) -> None:
            pipeline_slot.markdown(pipeline_html(lines, "running"), unsafe_allow_html=True)
            live_slot.code("\n".join(lines[-8:]), language="text")

        try:
            lines, returncode, elapsed, timed_out = run_engine(
                command, int(timeout) * 4 + 120, on_line
            )
            error_text = ""
        except OSError as exc:
            lines, returncode, elapsed, timed_out = [], -1, time.time() - started_at, False
            error_text = str(exc)

        live_slot.empty()
        st.session_state["repolens_run"] = {
            "lines": lines,
            "error": error_text,
            "returncode": returncode,
            "elapsed": elapsed,
            "timed_out": timed_out,
            "command": command,
            "started_at": started_at,
            "finished_at": time.strftime("%H:%M:%S"),
            "graph_provided": graph_path is not None,
            "preview_name": preview_name,
            "heuristic_only": heuristic_only,
        }

    run_data = st.session_state.get("repolens_run")
    report = read_report() if report_is_fresh(run_data) else None

    if run_data:
        lines = run_data.get("lines", [])
        returncode = run_data.get("returncode", -1)
        ok_run = returncode == 0 and not run_data.get("timed_out")
        pipeline_slot.markdown(
            pipeline_html(lines, "done" if ok_run else "failed"), unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Process", "Exited 0" if returncode == 0 else "Error")
        c2.metric("Duration", f'{run_data.get("elapsed", 0):.1f}s')
        c3.metric("Finished at", run_data.get("finished_at", "—"))

        if run_data.get("timed_out"):
            st.error("The process exceeded the total timeout. Increase the timeout or use a smaller repository.")
        if run_data.get("error"):
            st.error(f"Could not start the engine: {run_data['error']}")
        if not ok_run and not report:
            st.error("The engine did not produce a report. The last output lines are below.")

        with st.expander("Terminal output", expanded=not ok_run):
            st.code("\n".join(lines) if lines else "No output captured.", language="text")

    if report:
        target = report.get("target") or {}
        status = str(report.get("status", "UNKNOWN")).upper()
        original_pass = report.get("generated_tests_pass_original")
        mutation_detected = report.get("generated_tests_detect_mutation")
        lines = run_data.get("lines", [])

        def check_row(label: str, value) -> str:
            if value is True:
                icon, cls = "✓", "ok"
            elif value is False:
                icon, cls = "✗", "no"
            else:
                icon, cls = "?", "na"
            return (f'<div class="ev-row"><span class="ev-ic {cls}">{icon}</span>'
                    f'<span>{esc(label)}</span></div>')

        card_cls = "good" if status == "VERIFIED" else ("bad" if status in {"FAILED", "ERROR"} else "warn")
        source = detect_generation_source(report, lines)
        if source == "cached":
            source_pill = '<span class="status-pill status-warn">Replayed from cache — not a fresh Gemma call</span>'
        elif source == "live":
            source_pill = '<span class="status-pill status-good">Live model call</span>'
        elif run_data.get("heuristic_only"):
            source_pill = '<span class="status-pill">Heuristic-only run (no model)</span>'
        else:
            source_pill = '<span class="status-pill status-warn">Generation source not reported by engine</span>'

        graph_pill = (
            '<span class="status-pill">Graphify graph supplied to engine</span>'
            if run_data.get("graph_provided")
            else '<span class="status-pill">No Graphify graph supplied</span>'
        )
        dep_value = first_present(report, ("dependency_source", "graph_source", "graph_used", "used_graphify"))
        dep_pill = (
            f'<span class="status-pill">Dependency data: {esc(dep_value)}</span>' if dep_value is not None else ""
        )

        st.markdown(
            f"""
            <div class="evidence {card_cls}">
                <div class="ev-badge">{esc(status)}</div>
                {check_row("Generated tests pass on the original function", original_pass)}
                {check_row("Generated tests fail on the mutated function", mutation_detected)}
                <div class="ev-foot">{source_pill}{graph_pill}{dep_pill}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        engine_name = short_name(target)
        preview = run_data.get("preview_name", "")
        if engine_name and preview and engine_name != preview:
            st.warning(
                f"The engine chose **{engine_name}**, not the previewed **{preview}**. "
                "The engine's ranking decides which function is tested."
            )

        st.markdown('<div class="section-label">Selected function</div>', unsafe_allow_html=True)
        target_name = target.get("qualname") or target.get("name") or "Target not reported"
        st.markdown(
            f"""
            <div class="panel">
                <div style="font-family:var(--mono);font-size:1.02rem;color:#ddd6fe;font-weight:500;">{esc(target_name)}</div>
                <div class="panel-sub" style="margin-top:8px;">
                    {esc(target.get("file", "Unknown file"))} · line {esc(target.get("lineno", "—"))}
                    · complexity {esc(target.get("complexity", "—"))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        target_source = target.get("source", "")
        if target_source:
            st.markdown('<div class="section-label">The mutation</div>', unsafe_allow_html=True)
            stub = mutation_preview(target_source)
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("Original")
                st.code(target_source, language="python")
            with col_b:
                st.caption("Mutated copy (body replaced with `return None`)")
                if stub:
                    st.code(stub, language="python")
                else:
                    st.caption("Could not render a mutation preview for this function.")
            st.caption("Single-mutation check: it shows the tests react to this one change, "
                       "not that they catch every possible bug.")

        rows = ranking_rows(report)
        with st.expander("Candidate ranking", expanded=False):
            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.caption("This report does not include a candidate list.")

        with st.expander("Generated tests", expanded=True):
            test_code = safe_read(TEST_FILE)
            if test_code:
                st.code(test_code, language="python")
            else:
                st.caption("No generated test file was found in the output folder.")

        st.markdown('<div class="section-label">Artifacts</div>', unsafe_allow_html=True)
        download_cols = st.columns(3)
        download_cols[0].download_button(
            "↓  Report JSON",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name="repolens_report.json",
            mime="application/json",
            use_container_width=True,
        )
        test_code = safe_read(TEST_FILE)
        if test_code:
            download_cols[1].download_button(
                "↓  Generated tests", data=test_code,
                file_name="test_repolens_generated.py", mime="text/x-python",
                use_container_width=True,
            )
        else:
            download_cols[1].button("Generated tests unavailable", disabled=True, use_container_width=True)
        patch_text = safe_read(PATCH_FILE)
        if patch_text:
            download_cols[2].download_button(
                "↓  Tests patch", data=patch_text,
                file_name="tests.patch", mime="text/plain", use_container_width=True,
            )
        else:
            download_cols[2].button("Patch unavailable", disabled=True, use_container_width=True)

        st.info(
            "Scope limitation: VERIFIED applies only to the reported target and the specific "
            "mutation performed by this version of RepoLens. It does not prove full test "
            "coverage, general mutation resistance, or that the repository is bug-free. "
            "The engine's AST screening is not a secure execution sandbox."
        )

    elif not run_data:
        pipeline_slot.empty()
        st.markdown(
            """
            <div class="panel" style="margin-top:22px;padding:26px;">
                <div class="eyebrow">Ready when you are</div>
                <div style="font-size:1.2rem;font-weight:750;letter-spacing:-.035em;
                            margin:10px 0 7px;color:#f0eef8;">
                    Your next useful test starts here.
                </div>
                <div class="panel-sub">
                    Choose a function, then run the analysis. Each pipeline stage appears here as
                    the engine reports it, followed by the evidence and downloadable artifacts.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
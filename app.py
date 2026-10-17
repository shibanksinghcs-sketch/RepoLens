from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
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

st.set_page_config(
    page_title="RepoLens — Code Intelligence",
    page_icon="⌘",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styling ────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #101114;
        --panel: #17181d;
        --panel2: #1d1e25;
        --border: #2a2b35;
        --text: #efeff5;
        --muted: #9293a4;
        --violet: #a78bfa;
        --green: #65d6a0;
        --red: #ff7d91;
        --amber: #f4c77b;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(16,17,20,.88);
        border-bottom: 1px solid var(--border);
    }

    [data-testid="stSidebar"] {
        background: #141519;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem;
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }

    h1, h2, h3, p, label {
        color: var(--text);
    }

    h1 {
        font-size: 1.75rem !important;
        letter-spacing: -0.055em !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.15rem !important;
        letter-spacing: -0.025em !important;
    }

    h3 {
        font-size: .98rem !important;
    }

    [data-testid="stCaptionContainer"],
    .muted {
        color: var(--muted) !important;
    }

    code, pre, [data-testid="stCode"] {
        font-family: 'DM Mono', monospace !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextArea"] textarea {
        background: #111216 !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
        border-radius: 8px !important;
    }

    [data-testid="stButton"] button,
    [data-testid="stDownloadButton"] button {
        border-radius: 8px;
        min-height: 2.55rem;
        font-weight: 600;
        transition: border-color .15s ease, transform .15s ease;
    }

    [data-testid="stButton"] button[kind="primary"] {
        background: var(--violet);
        color: #17121f;
        border: 1px solid var(--violet);
    }

    [data-testid="stButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover {
        border-color: var(--violet);
        transform: translateY(-1px);
    }

    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        padding: 15px 17px;
        border-radius: 11px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: .78rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.55rem !important;
        font-weight: 750 !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        background: var(--panel);
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    hr {
        border-color: var(--border) !important;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 24px 0;
    }

    .brand-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 37px;
        height: 37px;
        border: 1px solid #51417b;
        background: #282138;
        color: #c4b5fd;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 800;
    }

    .brand-name {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -.04em;
        color: #f3f0ff;
    }

    .brand-sub {
        color: var(--muted);
        font-size: .7rem;
        margin-top: 1px;
    }

    .eyebrow {
        color: var(--violet);
        font-family: 'DM Mono', monospace;
        text-transform: uppercase;
        letter-spacing: .12em;
        font-size: .7rem;
        font-weight: 500;
    }

    .hero-title {
        font-size: clamp(1.65rem, 3vw, 2.4rem);
        line-height: 1.14;
        letter-spacing: -.06em;
        font-weight: 800;
        margin: 8px 0;
        color: #f5f3ff;
    }

    .hero-copy {
        color: #a3a3b4;
        font-size: .93rem;
        line-height: 1.65;
        max-width: 650px;
        margin-bottom: 20px;
    }

    .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 17px;
        margin-bottom: 14px;
    }

    .panel-heading {
        font-size: .9rem;
        font-weight: 700;
        color: #f1eff8;
        margin-bottom: 5px;
    }

    .panel-sub {
        color: var(--muted);
        font-size: .78rem;
        line-height: 1.5;
    }

    .file-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 8px;
        margin: 2px 0;
        color: #c4c4d1;
        font-family: 'DM Mono', monospace;
        font-size: .76rem;
        border-radius: 6px;
        overflow-wrap: anywhere;
    }

    .file-icon {
        color: #a78bfa;
        flex-shrink: 0;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 6px;
        font-family: 'DM Mono', monospace;
        font-size: .72rem;
        font-weight: 500;
        border: 1px solid var(--border);
        background: #202128;
        color: #c9c9d6;
    }

    .status-good {
        color: var(--green);
        border-color: #285c48;
        background: #142820;
    }

    .status-bad {
        color: var(--red);
        border-color: #683541;
        background: #2b171d;
    }

    .status-warn {
        color: var(--amber);
        border-color: #69522c;
        background: #292216;
    }

    .section-label {
        font-family: 'DM Mono', monospace;
        color: var(--muted);
        text-transform: uppercase;
        font-size: .68rem;
        letter-spacing: .1em;
        margin: 12px 0 8px;
    }

    div[data-testid="stVerticalBlock"] > div:has(> .element-container .hero-title) {
        gap: .2rem;
    }

    @media (max-width: 850px) {
        .block-container {
            padding: 1rem .85rem 2rem;
        }
        .hero-title {
            font-size: 1.7rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────

def resolve_path(raw_path: str) -> Path:
    """Resolve absolute paths or paths relative to the app directory."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def discover_python_files(repo: Path) -> list[Path]:
    """List Python files while hiding common generated and virtualenv folders."""
    ignored = {
        ".git", ".venv", "venv", "env", "__pycache__",
        "node_modules", ".mypy_cache", ".pytest_cache",
    }
    found = []
    try:
        for path in sorted(repo.rglob("*.py")):
            relative_parts = path.relative_to(repo).parts
            if any(part in ignored for part in relative_parts):
                continue
            found.append(path)
    except OSError:
        pass
    return found


def discover_top_level_functions(repo: Path) -> list[dict]:
    """
    Preview top-level functions in sorted Python files.
    This preview is informational; RepoLens itself determines the actual
    candidate ordering when the analysis runs.
    """
    candidates = []
    ignored = {
        ".git", ".venv", "venv", "env", "__pycache__",
        "node_modules", ".mypy_cache", ".pytest_cache",
    }

    for path in discover_python_files(repo):
        parts = path.relative_to(repo).parts
        lower_parts = [part.lower() for part in parts]

        if "tests" in lower_parts or "test" in lower_parts:
            continue
        if path.name.lower().startswith("test_"):
            continue
        if path.name.lower() == "conftest.py":
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidates.append({
                    "name": node.name,
                    "file": path.relative_to(repo).as_posix(),
                    "line": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
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
        with REPORT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def format_bool(value) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Not reported"


def status_class(status: str) -> str:
    if status == "VERIFIED":
        return "status-good"
    if status in {"FAILED", "ERROR"}:
        return "status-bad"
    return "status-warn"


def clear_previous_outputs() -> None:
    """Prevent an old report from being mistaken for the latest run."""
    for path in (REPORT_FILE, TEST_FILE, PATCH_FILE):
        try:
            if path.exists() and path.is_file():
                path.unlink()
        except OSError:
            pass


# ── Sidebar: repository explorer and settings ───────────────────

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
                    f'<span>{relative}</span></div>',
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
        "Per-command timeout",
        min_value=10,
        max_value=120,
        value=30,
        step=5,
        help="RepoLens may run multiple commands, so total run time can be longer.",
    )

    heuristic_only = st.toggle(
        "Heuristic-only mode",
        value=False,
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
        '<div class="panel-sub">Choose the candidate index passed to the existing engine '
        'using <code>--pick</code>.</div>',
        unsafe_allow_html=True,
    )

    candidates = discover_top_level_functions(repo_path) if repo_path.is_dir() else []

    if candidates:
        candidate_labels = [
            f"{i}  ·  {item['name']}  —  {item['file']}:{item['line']}"
            for i, item in enumerate(candidates)
        ]
        selected_label = st.selectbox(
            "Preview candidates",
            options=candidate_labels,
            index=0,
            help="This is an AST-based preview. The engine's own candidate ordering is authoritative.",
        )
        pick = candidate_labels.index(selected_label)

        chosen = candidates[pick]
        st.markdown(
            f"""
            <div class="panel">
                <div class="eyebrow">Selected preview</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.05rem;
                            font-weight:500;margin:9px 0;color:#ddd6fe;">
                    {chosen["name"]}
                </div>
                <div class="panel-sub">{chosen["file"]} · line {chosen["line"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        pick = st.number_input(
            "Function index (--pick)",
            min_value=0,
            value=0,
            step=1,
        )
        st.caption("No function preview is available. The engine will validate the index.")

    st.markdown('<div class="section-label">Before you run</div>', unsafe_allow_html=True)
    checks = [
        ("Engine", ENGINE.is_file()),
        ("Repository", repo_path.is_dir()),
        ("Python files", bool(discover_python_files(repo_path)) if repo_path.is_dir() else False),
    ]

    for label, passed in checks:
        icon_text = "✓" if passed else "!"
        color = "#65d6a0" if passed else "#f4c77b"
        st.markdown(
            f'<div class="file-row"><span style="color:{color};font-weight:800;">'
            f'{icon_text}</span><span>{label}</span></div>',
            unsafe_allow_html=True,
        )

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
        '<div class="panel-sub">Run the current engine, inspect its output, and download '
        'the generated artifacts. Analysis can take a few minutes.</div>',
        unsafe_allow_html=True,
    )

    if analyze_clicked:
        if not ENGINE.is_file():
            st.error(f"Engine not found: {ENGINE}")
        elif not repo_path.is_dir():
            st.error(f"Repository not found: {repo_path}")
        else:
            graph_path = None
            if graph_input.strip():
                graph_path = resolve_path(graph_input)
                if not graph_path.is_file():
                    st.error(f"Graph file not found: {graph_path}")
                    st.stop()

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            clear_previous_outputs()

            command = [
                sys.executable,
                str(ENGINE),
                str(repo_path),
                "--pick",
                str(int(pick)),
                "--timeout",
                str(int(timeout)),
                "--out",
                str(OUTPUT_DIR),
            ]

            if graph_path is not None:
                command.extend(["--graph", str(graph_path)])

            if heuristic_only:
                command.append("--no-llm")

            with st.status("Running RepoLens pipeline…", expanded=True) as status_box:
                st.write("Validating repository and selecting a function")
                st.code(" ".join(f'"{part}"' if " " in part else part for part in command))

                start_time = time.time()
                try:
                    result = subprocess.run(
                        command,
                        cwd=str(BASE_DIR),
                        capture_output=True,
                        text=True,
                        timeout=int(timeout) * 4 + 120,
                        check=False,
                        env=os.environ.copy(),
                    )
                    elapsed = time.time() - start_time

                    st.session_state["repolens_run"] = {
                        "stdout": result.stdout or "",
                        "stderr": result.stderr or "",
                        "returncode": result.returncode,
                        "elapsed": elapsed,
                        "command": command,
                        "finished_at": time.strftime("%H:%M:%S"),
                    }

                    if result.returncode == 0:
                        status_box.update(
                            label=f"Pipeline finished in {elapsed:.1f}s",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        status_box.update(
                            label=f"Engine exited with code {result.returncode}",
                            state="error",
                            expanded=True,
                        )

                except subprocess.TimeoutExpired as exc:
                    elapsed = time.time() - start_time
                    st.session_state["repolens_run"] = {
                        "stdout": exc.stdout or "",
                        "stderr": exc.stderr or "",
                        "returncode": -1,
                        "elapsed": elapsed,
                        "command": command,
                        "finished_at": time.strftime("%H:%M:%S"),
                        "timeout": True,
                    }
                    status_box.update(
                        label="Pipeline timed out",
                        state="error",
                        expanded=True,
                    )
                except OSError as exc:
                    st.session_state["repolens_run"] = {
                        "stdout": "",
                        "stderr": str(exc),
                        "returncode": -1,
                        "elapsed": time.time() - start_time,
                        "command": command,
                        "finished_at": time.strftime("%H:%M:%S"),
                    }
                    status_box.update(
                        label="Could not start RepoLens",
                        state="error",
                        expanded=True,
                    )

    run_data = st.session_state.get("repolens_run")
    report = read_report()

    if run_data:
        st.markdown('<div class="section-label">Execution</div>', unsafe_allow_html=True)
        col_status, col_time, col_code = st.columns(3)

        returncode = run_data.get("returncode", -1)
        col_status.metric("Process", "Exited 0" if returncode == 0 else "Error")
        col_time.metric("Duration", f'{run_data.get("elapsed", 0):.1f}s')
        col_code.metric("Exit code", str(returncode))

        with st.expander("Terminal output", expanded=returncode != 0):
            stdout = run_data.get("stdout", "")
            if stdout:
                st.code(stdout, language="text")
            else:
                st.caption("No standard output captured.")

        if run_data.get("stderr"):
            with st.expander("Warnings / errors", expanded=returncode != 0):
                st.code(str(run_data["stderr"]), language="text")

        if run_data.get("timeout"):
            st.error("The process exceeded the total timeout. Try increasing the timeout or using a smaller repository.")

    if report:
        target = report.get("target") or {}
        status = str(report.get("status", "UNKNOWN")).upper()
        original_pass = report.get("generated_tests_pass_original")
        mutation_detected = report.get("generated_tests_detect_mutation")

        st.divider()
        st.markdown('<div class="section-label">Verification report</div>', unsafe_allow_html=True)

        pill_class = status_class(status)
        st.markdown(
            f'<span class="status-pill {pill_class}">{status}</span>',
            unsafe_allow_html=True,
        )

        if status == "VERIFIED":
            st.success(
                "Generated tests passed on the original target and detected the specific "
                "mutation attempted by this engine."
            )
        elif status in {"FAILED", "ERROR"}:
            st.error("The report did not achieve a VERIFIED result. Inspect the run output below.")
        else:
            st.warning("The report status is not VERIFIED. Review the evidence before drawing conclusions.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Original tests passed", format_bool(original_pass))
        m2.metric("Mutation detected", format_bool(mutation_detected))
        m3.metric("Target complexity", target.get("complexity", "—"))

        st.markdown('<div class="panel-heading">Selected function</div>', unsafe_allow_html=True)
        target_name = target.get("qualname") or target.get("name") or "Target not reported"
        target_file = target.get("file", "Unknown file")
        target_line = target.get("lineno", "—")

        st.markdown(
            f"""
            <div class="panel">
                <div style="font-family:'DM Mono',monospace;font-size:1.02rem;
                            color:#ddd6fe;font-weight:500;">{target_name}</div>
                <div class="panel-sub" style="margin-top:8px;">
                    {target_file} · line {target_line}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Inspect target source", expanded=False):
            source = target.get("source", "")
            if source:
                st.code(source, language="python")
            else:
                st.caption("The report did not include target source.")

        with st.expander("Generated tests", expanded=True):
            test_code = safe_read(TEST_FILE)
            if test_code:
                st.code(test_code, language="python")
            else:
                st.caption("No generated test file was found in the output folder.")

        st.markdown('<div class="section-label">Artifacts</div>', unsafe_allow_html=True)
        download_cols = st.columns(3)

        report_text = json.dumps(report, indent=2, ensure_ascii=False)
        download_cols[0].download_button(
            "↓  Report JSON",
            data=report_text,
            file_name="repolens_report.json",
            mime="application/json",
            use_container_width=True,
        )

        test_code = safe_read(TEST_FILE)
        if test_code:
            download_cols[1].download_button(
                "↓  Generated tests",
                data=test_code,
                file_name="test_repolens_generated.py",
                mime="text/x-python",
                use_container_width=True,
            )
        else:
            download_cols[1].button(
                "Generated tests unavailable",
                disabled=True,
                use_container_width=True,
            )

        patch_text = safe_read(PATCH_FILE)
        if patch_text:
            download_cols[2].download_button(
                "↓  Tests patch",
                data=patch_text,
                file_name="tests.patch",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            download_cols[2].button(
                "Patch unavailable",
                disabled=True,
                use_container_width=True,
            )

        st.info(
            "Scope limitation: VERIFIED applies only to the reported target and the specific "
            "mutation performed by this version of RepoLens. It does not prove full test "
            "coverage, general mutation resistance, or that the repository is bug-free. "
            "The engine's AST screening is not a secure execution sandbox."
        )

    elif not run_data:
        st.markdown(
            """
            <div class="panel" style="margin-top:22px;padding:26px;">
                <div class="eyebrow">Ready when you are</div>
                <div style="font-size:1.2rem;font-weight:750;letter-spacing:-.035em;
                            margin:10px 0 7px;color:#f0eef8;">
                    Your next useful test starts here.
                </div>
                <div class="panel-sub">
                    Choose a function in the repository explorer, then run the analysis.
                    RepoLens will report the actual engine output and available artifacts here.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
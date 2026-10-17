# RepoLens

**AI-assisted Python test generation with mutation-based verification.**

RepoLens analyzes Python functions, ranks candidate targets using dependency information when available, generates focused `pytest` tests through the Gemini API, and checks whether those tests detect a deliberate code mutation.

## Features

- Python function discovery and candidate ranking
- Optional Graphify dependency-graph input
- AI-generated pytest tests using a Gemma model through the Gemini API
- AST-based screening of generated test code
- Tests run against the original function and a deliberately mutated version
- JSON reports, generated test files, and patch outputs
- Streamlit dashboard for running and reviewing analyses

## How Verification Works

RepoLens runs generated tests against the original target and then against a version where the selected function body is replaced with `return None`.

**`VERIFIED` means the generated tests passed on the original target and detected this specific mutation.**

It does not prove complete test coverage, correctness, security, or the absence of bugs.

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`
- A Gemini API key for AI-powered test generation
- Optional Graphify output for dependency-based ranking

## Installation on Windows

### 1. Clone the repository

After publishing this project to GitHub, run:

```cmd
git clone YOUR_GITHUB_REPOSITORY_URL
cd RepoLens
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Install dependencies

```cmd
python -m pip install -r requirements.txt
```

### 3. Configure AI test generation

Set your Gemini API key in the current CMD session:

```cmd
set GEMINI_API_KEY=YOUR_API_KEY_HERE
set GEMMA_BACKEND=gemini
set GEMMA_MODEL=gemma-4-26b-a4b-it
```

Replace `YOUR_API_KEY_HERE` with your own API key. Never commit or publish API keys.

These environment variables apply to the current CMD session. Set them again when opening a new session.

### 4. Launch the dashboard

```cmd
python -m streamlit run app.py
```

Streamlit will provide a local URL to open in your browser.

## Usage

### Run the included demo

From the RepoLens project directory:

```cmd
python repolens.py demo-repo
```

This runs the engine against the included demo repository. AI-powered generation requires a valid Gemini API key and network access.

### View command-line options

```cmd
python repolens.py --help
```

### Optional dependency graph

RepoLens can use Graphify dependency data when available to help rank candidate functions. If graph data is unavailable, it can use fallback heuristics.

## Demo Repository

The included `demo-repo` contains a score classifier, a score-normalization function, and an existing test example.

The classifier demonstrates boundary-focused tests, while the normalization function demonstrates ordinary inputs and invalid-parameter handling.

## Limitations

- AI-generated tests can be incomplete, incorrect, or overly narrow.
- Gemini API-based generation requires network access and a valid API key.
- AST-based screening is not a secure sandbox.
- Execution timeouts do not guarantee safe isolation of untrusted code.
- The current mutation strategy is limited and can be relatively easy for tests to detect.
- Dependency-based ranking depends on the quality and availability of Graphify data; fallback heuristics may be used.
- Results depend on the selected function, generated tests, runtime environment, and mutation applied.

## Security

Use RepoLens only on code you are authorized to analyze. Review generated tests and patches before using them in a production project.

Never commit API keys, environment files containing secrets, or sensitive repository data.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
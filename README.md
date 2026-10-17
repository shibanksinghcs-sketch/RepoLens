# RepoLens

**AI-Assisted Python Test Generation with Mutation-Based Verification**

RepoLens is a Python developer tool that uses AI to generate focused unit tests and evaluates whether those tests can detect a deliberate code mutation. It combines function analysis, candidate ranking, AI-generated `pytest` tests, and mutation-based verification in a CLI engine and Streamlit dashboard.

The goal is simple: help developers move beyond generating tests to checking whether those tests catch at least one meaningful failure.

## Features

- **Python function discovery** — identify functions that can be targeted for testing.
- **Candidate ranking** — prioritize functions using dependency information when available and fallback heuristics otherwise.
- **AI-powered test generation** — generate focused `pytest` tests using a Gemma model through the Gemini API.
- **AST-based screening** — screen generated test code before execution.
- **Mutation-based verification** — check generated tests against the original function and a deliberately mutated version.
- **CLI and web dashboard** — use the command-line engine or Streamlit interface.
- **Reports and patches** — produce analysis outputs, JSON reports, generated test files, and patch outputs.
- **Demo repository** — explore the workflow using included sample Python functions.

## How It Works

1. **Analyze:** discover Python functions in the target repository.
2. **Prioritize:** rank candidate functions using available dependency data or fallback heuristics.
3. **Generate:** ask the configured AI model to produce focused unit tests.
4. **Screen:** apply AST-based checks to the generated test code.
5. **Execute:** run the generated tests against the original target.
6. **Mutate:** replace the selected function body with a deliberate mutation, currently `return None`.
7. **Verify:** check whether the tests pass on the original target and detect the selected mutation.
8. **Report:** review the results and generated artifacts.

### Understanding `VERIFIED`

**`VERIFIED` means the generated tests passed on the original target and detected the specific mutation applied by RepoLens.**

It does **not** establish complete test coverage, overall program correctness, security, or the absence of bugs. Mutation detection depends on the selected function, generated tests, and mutation strategy.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core engine and analysis |
| Streamlit | Interactive dashboard |
| Gemini API / Gemma model | AI-assisted test generation |
| pytest | Test execution |
| Python AST | Function analysis and test-code screening |
| JSON | Structured reports |
| Git | Version control |

## Project Structure

```text
RepoLens/
├── app.py                     # Streamlit dashboard
├── repolens.py                # CLI analysis and verification engine
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── LICENSE                    # MIT License
├── .gitignore                 # Excluded files and generated artifacts
└── demo-repo/
    ├── classifier.py          # Example functions under test
    └── tests/
        └── test_classifier.py # Example test file
```

Generated outputs and local cache files may be created when running the project.

## Requirements

- Python 3.10 or newer
- pip
- A Gemini API key for AI-powered test generation
- Internet access for API-based generation
- Windows, Linux, or macOS with a compatible Python environment

## Installation on Windows

### 1. Clone the repository

Open Command Prompt (CMD) and run:

```cmd
git clone https://github.com/shibanksinghcs-sketch/RepoLens.git
cd RepoLens
```

### 2. Install dependencies

```cmd
python -m pip install -r requirements.txt
```

### 3. Configure the Gemini API

Set your API key and model configuration in the current CMD session:

```cmd
set GEMINI_API_KEY=YOUR_API_KEY_HERE
set GEMMA_BACKEND=gemini
set GEMMA_MODEL=gemma-4-26b-a4b-it
```

Replace `YOUR_API_KEY_HERE` with your own API key. Do not share or commit your actual key.

These variables apply only to the current CMD session. Configure them again in a new session before using AI-powered generation.

### 4. Launch the dashboard

```cmd
python -m streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

## Usage

### Run the included demo

From the project directory:

```cmd
python repolens.py demo-repo
```

The demo exercises the analysis and testing workflow. AI-powered generation requires a valid API configuration and network access.

### View command-line options

```cmd
python repolens.py --help
```

### Use the dashboard

```cmd
python -m streamlit run app.py
```

Use the dashboard to interact with the analysis workflow and review the results supported by the current implementation.

## Demo Repository

The included `demo-repo` provides example classifier and score-normalization functions alongside a sample test file.

It is intended to demonstrate function targeting, boundary-focused test generation, and mutation-based verification. Results from this small demo should not be treated as evidence of performance across arbitrary production repositories.

## Limitations

- AI-generated tests can be incomplete, incorrect, redundant, or overly narrow.
- AI-powered generation requires a working API configuration and network access.
- AST-based screening is not a secure sandbox.
- Execution timeouts do not guarantee safe isolation of untrusted code.
- The current mutation strategy is limited and may be easy for some tests to detect.
- Dependency-based ranking depends on the quality and availability of Graphify data; fallback heuristics may be used.
- Results depend on the target code, generated tests, runtime environment, and mutation applied.

## Security

- Analyze only repositories and code you are authorized to use.
- Review generated tests, reports, and patches before applying them.
- Never commit API keys, `.env` files containing secrets, or sensitive repository data.
- Do not treat AST screening as a security boundary for untrusted code.

## Roadmap

Potential future improvements include:

- More mutation operators and mutation score reporting
- Improved test-quality and edge-case analysis
- Broader language and framework support
- Stronger process isolation for executing generated code
- Better dependency-graph integration
- CI integration and automated regression testing
- More detailed test reports and reproducible experiment summaries

These are planned directions, not claims about existing functionality.

## Contributing

Contributions, bug reports, and suggestions are welcome. Please describe the problem, steps to reproduce it, and the expected behavior when opening an issue or proposing a change.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Author

Created by **Shivank Singh**.

GitHub: [@shibanksinghcs-sketch](https://github.com/shibanksinghcs-sketch)

---

*RepoLens — Generate tests. Challenge them. Measure what they catch.*

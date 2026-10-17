[1mdiff --git a/README.md b/README.md[m
[1mindex 84696e0..fcff622 100644[m
[1m--- a/README.md[m
[1m+++ b/README.md[m
[36m@@ -1,56 +1,97 @@[m
 # RepoLens[m
 [m
[31m-**AI-assisted Python test generation with mutation-based verification.**[m
[32m+[m[32m**AI-Assisted Python Test Generation with Mutation-Based Verification**[m
 [m
[31m-RepoLens analyzes Python functions, ranks candidate targets using dependency information when available, generates focused `pytest` tests through the Gemini API, and checks whether those tests detect a deliberate code mutation.[m
[32m+[m[32mRepoLens is a Python developer tool that uses AI to generate focused unit tests and evaluates whether those tests can detect a deliberate code mutation. It combines function analysis, candidate ranking, AI-generated `pytest` tests, and mutation-based verification in a CLI engine and Streamlit dashboard.[m
 [m
[31m-## Features[m
[31m-[m
[31m-- Python function discovery and candidate ranking[m
[31m-- Optional Graphify dependency-graph input[m
[31m-- AI-generated pytest tests using a Gemma model through the Gemini API[m
[31m-- AST-based screening of generated test code[m
[31m-- Tests run against the original function and a deliberately mutated version[m
[31m-- JSON reports, generated test files, and patch outputs[m
[31m-- Streamlit dashboard for running and reviewing analyses[m
[31m-[m
[31m-## How Verification Works[m
[32m+[m[32mThe goal is simple: help developers move beyond generating tests to checking whether those tests catch at least one meaningful failure.[m
 [m
[31m-RepoLens runs generated tests against the original target and then against a version where the selected function body is replaced with `return None`.[m
[32m+[m[32m## Features[m
 [m
[31m-**`VERIFIED` means the generated tests passed on the original target and detected this specific mutation.**[m
[32m+[m[32m- **Python function discovery** — identify functions that can be targeted for testing.[m
[32m+[m[32m- **Candidate ranking** — prioritize functions using dependency information when available and fallback heuristics otherwise.[m
[32m+[m[32m- **AI-powered test generation** — generate focused `pytest` tests using a Gemma model through the Gemini API.[m
[32m+[m[32m- **AST-based screening** — screen generated test code before execution.[m
[32m+[m[32m- **Mutation-based verification** — check generated tests against the original function and a deliberately mutated version.[m
[32m+[m[32m- **CLI and web dashboard** — use the command-line engine or Streamlit interface.[m
[32m+[m[32m- **Reports and patches** — produce analysis outputs, JSON reports, generated test files, and patch outputs.[m
[32m+[m[32m- **Demo repository** — explore the workflow using included sample Python functions.[m
[32m+[m
[32m+[m[32m## How It Works[m
[32m+[m
[32m+[m[32m1. **Analyze:** discover Python functions in the target repository.[m
[32m+[m[32m2. **Prioritize:** rank candidate functions using available dependency data or fallback heuristics.[m
[32m+[m[32m3. **Generate:** ask the configured AI model to produce focused unit tests.[m
[32m+[m[32m4. **Screen:** apply AST-based checks to the generated test code.[m
[32m+[m[32m5. **Execute:** run the generated tests against the original target.[m
[32m+[m[32m6. **Mutate:** replace the selected function body with a deliberate mutation, currently `return None`.[m
[32m+[m[32m7. **Verify:** check whether the tests pass on the original target and detect the selected mutation.[m
[32m+[m[32m8. **Report:** review the results and generated artifacts.[m
[32m+[m
[32m+[m[32m### Understanding `VERIFIED`[m
[32m+[m
[32m+[m[32m**`VERIFIED` means the generated tests passed on the original target and detected the specific mutation applied by RepoLens.**[m
[32m+[m
[32m+[m[32mIt does **not** establish complete test coverage, overall program correctness, security, or the absence of bugs. Mutation detection depends on the selected function, generated tests, and mutation strategy.[m
[32m+[m
[32m+[m[32m## Tech Stack[m
[32m+[m
[32m+[m[32m| Technology | Purpose |[m
[32m+[m[32m|---|---|[m
[32m+[m[32m| Python | Core engine and analysis |[m
[32m+[m[32m| Streamlit | Interactive dashboard |[m
[32m+[m[32m| Gemini API / Gemma model | AI-assisted test generation |[m
[32m+[m[32m| pytest | Test execution |[m
[32m+[m[32m| Python AST | Function analysis and test-code screening |[m
[32m+[m[32m| JSON | Structured reports |[m
[32m+[m[32m| Git | Version control |[m
[32m+[m
[32m+[m[32m## Project Structure[m
[32m+[m
[32m+[m[32m```text[m
[32m+[m[32mRepoLens/[m
[32m+[m[32m├── app.py                     # Streamlit dashboard[m
[32m+[m[32m├── repolens.py                # CLI analysis and verification engine[m
[32m+[m[32m├── requirements.txt           # Python dependencies[m
[32m+[m[32m├── README.md                  # Project documentation[m
[32m+[m[32m├── LICENSE                    # MIT License[m
[32m+[m[32m├── .gitignore                 # Excluded files and generated artifacts[m
[32m+[m[32m└── demo-repo/[m
[32m+[m[32m    ├── classifier.py          # Example functions under test[m
[32m+[m[32m    └── tests/[m
[32m+[m[32m        └── test_classifier.py # Example test file[m
[32m+[m[32m```[m
 [m
[31m-It does not prove complete test coverage, correctness, security, or the absence of bugs.[m
[32m+[m[32mGenerated outputs and local cache files may be created when running the project.[m
 [m
 ## Requirements[m
 [m
 - Python 3.10 or newer[m
[31m-- Dependencies listed in `requirements.txt`[m
[32m+[m[32m- pip[m
 - A Gemini API key for AI-powered test generation[m
[31m-- Optional Graphify output for dependency-based ranking[m
[32m+[m[32m- Internet access for API-based generation[m
[32m+[m[32m- Windows, Linux, or macOS with a compatible Python environment[m
 [m
 ## Installation on Windows[m
 [m
 ### 1. Clone the repository[m
 [m
[31m-After publishing this project to GitHub, run:[m
[32m+[m[32mOpen Command Prompt (CMD) and run:[m
 [m
 ```cmd[m
[31m-git clone YOUR_GITHUB_REPOSITORY_URL[m
[32m+[m[32mgit clone https://github.com/shibanksinghcs-sketch/RepoLens.git[m
 cd RepoLens[m
 ```[m
 [m
[31m-Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.[m
[31m-[m
 ### 2. Install dependencies[m
 [m
 ```cmd[m
 python -m pip install -r requirements.txt[m
 ```[m
 [m
[31m-### 3. Configure AI test generation[m
[32m+[m[32m### 3. Configure the Gemini API[m
 [m
[31m-Set your Gemini API key in the current CMD session:[m
[32m+[m[32mSet your API key and model configuration in the current CMD session:[m
 [m
 ```cmd[m
 set GEMINI_API_KEY=YOUR_API_KEY_HERE[m
[36m@@ -58,9 +99,9 @@[m [mset GEMMA_BACKEND=gemini[m
 set GEMMA_MODEL=gemma-4-26b-a4b-it[m
 ```[m
 [m
[31m-Replace `YOUR_API_KEY_HERE` with your own API key. Never commit or publish API keys.[m
[32m+[m[32mReplace `YOUR_API_KEY_HERE` with your own API key. Do not share or commit your actual key.[m
 [m
[31m-These environment variables apply to the current CMD session. Set them again when opening a new session.[m
[32m+[m[32mThese variables apply only to the current CMD session. Configure them again in a new session before using AI-powered generation.[m
 [m
 ### 4. Launch the dashboard[m
 [m
[36m@@ -68,19 +109,19 @@[m [mThese environment variables apply to the current CMD session. Set them again whe[m
 python -m streamlit run app.py[m
 ```[m
 [m
[31m-Streamlit will provide a local URL to open in your browser.[m
[32m+[m[32mOpen the local URL printed by Streamlit in your browser.[m
 [m
 ## Usage[m
 [m
 ### Run the included demo[m
 [m
[31m-From the RepoLens project directory:[m
[32m+[m[32mFrom the project directory:[m
 [m
 ```cmd[m
 python repolens.py demo-repo[m
 ```[m
 [m
[31m-This runs the engine against the included demo repository. AI-powered generation requires a valid Gemini API key and network access.[m
[32m+[m[32mThe demo exercises the analysis and testing workflow. AI-powered generation requires a valid API configuration and network access.[m
 [m
 ### View command-line options[m
 [m
[36m@@ -88,32 +129,65 @@[m [mThis runs the engine against the included demo repository. AI-powered generation[m
 python repolens.py --help[m
 ```[m
 [m
[31m-### Optional dependency graph[m
[32m+[m[32m### Use the dashboard[m
[32m+[m
[32m+[m[32m```cmd[m
[32m+[m[32mpython -m streamlit run app.py[m
[32m+[m[32m```[m
 [m
[31m-RepoLens can use Graphify dependency data when available to help rank candidate functions. If graph data is unavailable, it can use fallback heuristics.[m
[32m+[m[32mUse the dashboard to interact with the analysis workflow and review the results supported by the current implementation.[m
 [m
 ## Demo Repository[m
 [m
[31m-The included `demo-repo` contains a score classifier, a score-normalization function, and an existing test example.[m
[32m+[m[32mThe included `demo-repo` provides example classifier and score-normalization functions alongside a sample test file.[m
 [m
[31m-The classifier demonstrates boundary-focused tests, while the normalization function demonstrates ordinary inputs and invalid-parameter handling.[m
[32m+[m[32mIt is intended to demonstrate function targeting, boundary-focused test generation, and mutation-based verification. Results from this small demo should not be treated as evidence of performance across arbitrary production repositories.[m
 [m
 ## Limitations[m
 [m
[31m-- AI-generated tests can be incomplete, incorrect, or overly narrow.[m
[31m-- Gemini API-based generation requires network access and a valid API key.[m
[32m+[m[32m- AI-generated tests can be incomplete, incorrect, redundant, or overly narrow.[m
[32m+[m[32m- AI-powered generation requires a working API configuration and network access.[m
 - AST-based screening is not a secure sandbox.[m
 - Execution timeouts do not guarantee safe isolation of untrusted code.[m
[31m-- The current mutation strategy is limited and can be relatively easy for tests to detect.[m
[32m+[m[32m- The current mutation strategy is limited and may be easy for some tests to detect.[m
 - Dependency-based ranking depends on the quality and availability of Graphify data; fallback heuristics may be used.[m
[31m-- Results depend on the selected function, generated tests, runtime environment, and mutation applied.[m
[32m+[m[32m- Results depend on the target code, generated tests, runtime environment, and mutation applied.[m
 [m
 ## Security[m
 [m
[31m-Use RepoLens only on code you are authorized to analyze. Review generated tests and patches before using them in a production project.[m
[32m+[m[32m- Analyze only repositories and code you are authorized to use.[m
[32m+[m[32m- Review generated tests, reports, and patches before applying them.[m
[32m+[m[32m- Never commit API keys, `.env` files containing secrets, or sensitive repository data.[m
[32m+[m[32m- Do not treat AST screening as a security boundary for untrusted code.[m
 [m
[31m-Never commit API keys, environment files containing secrets, or sensitive repository data.[m
[32m+[m[32m## Roadmap[m
[32m+[m
[32m+[m[32mPotential future improvements include:[m
[32m+[m
[32m+[m[32m- More mutation operators and mutation score reporting[m
[32m+[m[32m- Improved test-quality and edge-case analysis[m
[32m+[m[32m- Broader language and framework support[m
[32m+[m[32m- Stronger process isolation for executing generated code[m
[32m+[m[32m- Better dependency-graph integration[m
[32m+[m[32m- CI integration and automated regression testing[m
[32m+[m[32m- More detailed test reports and reproducible experiment summaries[m
[32m+[m
[32m+[m[32mThese are planned directions, not claims about existing functionality.[m
[32m+[m
[32m+[m[32m## Contributing[m
[32m+[m
[32m+[m[32mContributions, bug reports, and suggestions are welcome. Please describe the problem, steps to reproduce it, and the expected behavior when opening an issue or proposing a change.[m
 [m
 ## License[m
 [m
[31m-This project is licensed under the MIT License. See [LICENSE](LICENSE).[m
\ No newline at end of file[m
[32m+[m[32mThis project is licensed under the MIT License. See [LICENSE](LICENSE).[m
[32m+[m
[32m+[m[32m## Author[m
[32m+[m
[32m+[m[32mCreated by **Shivank Singh**.[m
[32m+[m
[32m+[m[32mGitHub: [@shibanksinghcs-sketch](https://github.com/shibanksinghcs-sketch)[m
[32m+[m
[32m+[m[32m---[m
[32m+[m
[32m+[m[32m*RepoLens — Generate tests. Challenge them. Measure what they catch.*[m

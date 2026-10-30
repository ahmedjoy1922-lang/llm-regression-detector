
# 🛡️ LLM Regression Detector & Automated CI/CD Safety Gate

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Testing Framework](https://img.shields.io/badge/tested%20with-pytest-blueviolet)](https://docs.pytest.org/)
[![Data Validation](https://img.shields.io/badge/schema-pydantic-red)](https://docs.pydantic.dev/)
[![CI/CD Pipeline](https://img.shields.io/badge/pipeline-GitHub%20Actions-green)](https://github.com/features/actions)

An enterprise-grade, deterministic regression testing suite and command-line quality gate for LLM prompt templates. This project implements a software-engineered approach to LLM application development, transitioning from "vibes-based" prompt validation to structured, automated, and continuous integration evaluation.

---

## 🎯 The Problem

When developing applications powered by LLMs, a major challenge is **Prompt Regression**. Modifying a system prompt template to fix a specific bug (e.g., improving classification for a billing issue) can silently degrade performance in unrelated categories (e.g., technical troubleshooting or account access).

Because LLMs are non-deterministic and highly adaptive, they often rely on pre-trained semantic instincts to mask subtle prompt defects. Traditional unit tests fail to catch these drift issues, making manual evaluation slow, expensive, and unsafe for production releases.

## 🛠️ The Solution

This project implements a **local, offline-first LLM evaluation engine and custom CLI Quality Gate** that integrates directly into GitHub Actions. 

It validates model performance against a **Golden Dataset** of structured support tickets. If any prompt change results in an accuracy drop, latency spike, or token usage increase that violates configured business thresholds, the quality gate triggers a non-zero exit code to automatically block the release pipeline.

---

## ✨ Key Features

- **Pydantic Data Contracts:** Strongly typed data schemas for datasets, model runs, prompt settings, and evaluation metrics using Pydantic V2.
- **Offline Test Fixtures:** Pre-computed and frozen baseline, degraded, and candidate runs allowing full offline verification without incurring API cost or latency.
- **Strict Constraint Mutation:** Overrides Gemini's semantic instincts during negative testing using strict instruction-mapping overrides.
- **Automated CLI Quality Gate:** A configurable, lightweight CLI engine (`gate_cli.py`) that reads validation policies from a `policy.yaml` configuration.
- **Continuous Integration:** Fully integrated GitHub Actions workflow that executes Pytest suites and enforces prompt regression gates on every push.
- **Trend Telemetry Dashboard:** Generates an HTML report mapping historical accuracy trends and identifying precise failing slices.

---

## 🏗️ System Architecture

```text
llm-regression-detector/
├── .github/workflows/          # CI/CD pipelines
│   └── regression-gate.yml     # Automated safety gate workflow
├── data/
│   └── golden.json             # 18-case Golden Evaluation Dataset
├── prompts/
│   └── classifier-v2.yaml      # System Prompt Template config
├── reports/
│   └── gate.json               # Generated execution report
├── runs/
│   ├── baseline.json           # Approved reference run
│   └── degraded.json           # Intentionally mutated failing run
├── src/
│   └── regression_detector/
│       ├── analysis.py         # Slice analysis and helper utilities
│       ├── compare.py          # Run comparison logic & diff calculator
│       ├── dataset.py          # Golden dataset loading utilities
│       ├── domain.py           # Core Pydantic domain models
│       ├── evaluator.py        # Gemini API execution wrapper
│       ├── gate.py             # Evaluation quality gate policy engine
│       ├── gate_cli.py         # Command-line interface for the quality gate
│       └── run_models.py       # Pydantic schemas for execution records
├── tests/
│   ├── fixtures/               # Frozen runs for reproducible testing
│   ├── test_gate.py            # Unit tests for gate policy logic
│   ├── test_regression_contracts.py # Offline contract validation tests
│   └── test_validation_contracts.py # Schema validation unit tests
├── policy.yaml                 # Configurable business safety thresholds
└── requirements.txt            # Project dependencies
```

---

## 🚦 Getting Started (Local Setup)

This project has been developed and tested on **Windows 11** using PowerShell.

### 1. Clone & Set Up Virtual Environment
```powershell
# Clone the repository
git clone https://github.com/your-username/llm-regression-detector.git
cd llm-regression-detector

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory and add your API credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Offline Pytest Verification Suite
Verify that all core business contracts, validation schemas, and policies are fully operational:
```powershell
python -m pytest -q
```

---

## 📈 Running the Evaluation & Gate

### Step 1: Run Prompt Evaluation
Compile metrics against the Golden Dataset and generate a fresh candidate run:
```powershell
python -m regression_detector.evaluator
```

### Step 2: Enforce the Regression Gate Locally
Evaluate the fresh candidate run against your baseline run using the threshold policy defined in `policy.yaml`:
```powershell
python -m regression_detector.gate_cli --baseline-path tests/fixtures/baseline.json --candidate-path tests/fixtures/candidate.json
```

---

## 📊 Configurable Business Policies (`policy.yaml`)

Our quality gate is driven by a YAML configuration file. You can easily tweak accuracy, token, and latency safety limits to fit different business requirements:

```yaml
warning_accuracy_drop: 0.01          # Warn if accuracy drops by >1%
critical_accuracy_drop: 0.05         # Hard block if accuracy drops by >5%
critical_regression_count: 2         # Hard block if 2 or more tests fail
warning_token_increase: 0.25         # Warn if LLM tokens grow by >25%
warning_p95_latency_increase: 1.50   # Warn if p95 latency spikes by >150% (network tolerance)
```

---

## ⚙️ Automated CI/CD Pipeline (GitHub Actions)

This project features a fully automated workflow that blocks invalid prompt templates from reaching production.

When a developer modifies a prompt template or source code:
1. **GitHub Actions** provisions a clean Linux container.
2. The code, datasets, and frozen fixtures are checked out.
3. **Pytest** is run to confirm backend compatibility.
4. The **CLI Quality Gate** runs automatically.
5. If the comparison engine returns a status of `WARN` or `CRITICAL` (due to poor accuracy or latency spikes), the script raises exit code `1` or `2` which **intentionally fails the build** and stops any downstream deploy steps.

---

## 💡 Engineering Insights & Key Takeaways

1. **Managing Semantic Instincts:** Modern models like Gemini are highly resilient and will "auto-correct" weaker prompt defects using pre-trained knowledge. Testing an LLM pipeline requires strict, explicit constraints to bypass this resilience during negative evaluation tests.
2. **Network Tolerance in CI/CD:** Hard-coding strict latency limits can make build pipelines "flaky" due to normal internet routing noise. Separating correctness metrics (hard blocking) from performance warning metrics (elastic thresholds) is essential for maintainable pipelines.
3. **Reproducible Test Fixtures:** Storing local, pre-evaluated JSON execution fixtures enables us to run incredibly fast regression tests completely offline, eliminating expensive API usage in testing environments.

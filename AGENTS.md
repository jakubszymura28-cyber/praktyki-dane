# AGENTS.md

Instructions and guidelines for AI agents working in this repository.

## 📌 Project Overview
- **Project Name:** Praktyki - Analiza Danych
- **Description:** Opanowanie narzędzi analitycznych, automatyzacja pracy z danymi oraz efektywna współpraca z asystentami AI w środowisku IDE.

---

## 🛠️ Tech Stack & Environment
- **Language:** Python 3.10+ (or current installed version)
- **Virtual Environment:** `.venv` (`python -m venv .venv`)
- **Common Libraries:** `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `jupyter`
- **Dependency Management:** `requirements.txt`

---

## 📁 Recommended Repository Structure
```text
praktyki dane/
├── data/
│   ├── raw/            # Original, read-only raw datasets
│   └── processed/      # Cleaned and prepared data ready for analysis
├── notebooks/          # Jupyter notebooks for EDA and prototyping
├── src/                # Reusable source code, data pipelines, utilities
├── outputs/            # Exported figures, charts, models, and reports
├── requirements.txt    # Project dependencies
├── AGENTS.md           # Instructions and rules for AI assistants
└── README.md           # Human-facing project documentation
```

---

## 📋 Rules & Guidelines for AI Agents

### 1. Data Integrity & Safety
- **Never mutate raw data:** Files in `data/raw/` must remain untouched. All transformations should be written to `data/processed/`.
- **Sensitive Data:** Never hardcode credentials, API tokens, or commit private personally identifiable information (PII).

### 2. Code Quality & Modularity
- Write clean, PEP 8-compliant Python code with type annotations where helpful.
- Keep exploratory code in notebooks, but refactor recurring functions and pipeline steps into `src/` modules.
- Ensure scripts and pipelines are deterministic by setting random seeds (e.g., `seed=42` / `random_state=42`).

### 3. Workflow & Best Practices
- When proposing major changes or starting new pipelines, provide clear explanations and verify outputs.
- Keep `requirements.txt` updated when introducing new packages.
- Always check and validate data schemas (column names, types, null values) before running computations.

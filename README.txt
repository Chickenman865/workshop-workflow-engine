### The `README.md`

```markdown
# Workshop Workflow Engine

A deterministic diagnostic engine for automotive repair that minimizes LLM hallucinations by separating **Perception** from **Execution**.

## The Problem
Most AI diagnostic agents are "black boxes" that take a query and return an answer, often hallucinating technical data or recommending unsafe repairs. In automotive diagnostics, a small error can result in thousands of dollars in misdiagnosed parts.

## The Solution: A Deterministic FSM
This project treats the LLM purely as a **Perception Layer**. It extracts structured facts from natural language, which are then passed through a **Deterministic Gatekeeper** and a **Finite State Machine (FSM)**. If the data is ambiguous, contradictory, or missing, the system forces a re-test rather than guessing.

### Core Architecture


## Features
- **Data-Driven Evaluation:** Nodes define their own `accepted_fact_keys`, making the system easily scalable for thousands of procedures.
- **Unit-Aware Extraction:** Regex pre-parser identifies units (V, Ohms, Amps) before the LLM even sees the input.
- **Loop-Back FSM:** If the technician provides invalid evidence (e.g., voltages when a status is expected), the system refuses to proceed and prompts for a re-test.
- **Explainable Audit Trail:** Every decision is logged with a `decision_reason`, providing full transparency for debugging.

## Setup
This project expects a specific directory structure to maintain session logs.

1. Create your project folder:
   ```bash
   mkdir C:\AI\Projects\workshop_engine
   cd C:\AI\Projects\workshop_engine

```

2. Clone this repository into that folder.
3. Ensure you have [Ollama](https://ollama.com/) running locally.
4. Install dependencies:
```bash
pip install pydantic requests

```


5. Run the engine:
```bash
python run_diagnostic.py

```



## Requirements

* **LLM Backend:** Ollama (defaulting to `qwen3:8b`).
* **Python:** 3.10+

## License

MIT
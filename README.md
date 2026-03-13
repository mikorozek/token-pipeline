# Cross-Chain Token Pipeline

This project discovers token deployments across chains, checks bridge availability, gathers chain and audit context, and produces a final report for a given token contract.

It was built using `ai-pipeline-core`.

## What It Does

The pipeline runs these stages:

1. Resolve the input token and gather known deployments across chains.
2. Collect bridge protocol and route information between deployments.
3. Generate transfer instructions for supported routes.
4. Research destination chain security and maturity.
5. Research audits for the token, related chains, and bridge protocols.
6. Produce a final report.

## Requirements

- Python 3.12+
- `uv`
- LLM access configured via environment variables

## Environment

At minimum, configure:

```env
OPENAI_BASE_URL=...
OPENAI_API_KEY=...
```

Optional:

```env
LMNR_PROJECT_API_KEY=...
```

## Installation

Create a local virtual environment inside the project and install `ai-pipeline-core` in editable mode:

```bash
cd cross_chain_token_pipeline
uv venv
uv pip install --python .venv/bin/python -e ../ai-pipeline-core
```

The application itself does not need editable installation for local runs. Run it from the parent workspace directory so Python can import the package directly from source.

## Usage

From the workspace root:

```bash
cross_chain_token_pipeline/.venv/bin/python -m cross_chain_token_pipeline ./out-token \
  --contract-address 0x... \
  --chain-name bsc
```

Example:

```bash
cross_chain_token_pipeline/.venv/bin/python -m cross_chain_token_pipeline ./out-cake \
  --contract-address 0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82 \
  --chain-name bsc
```

## Output

The output directory contains:

- `result.json` with the run result envelope
- typed intermediate artifacts such as deployments and bridges
- the final Markdown report
- `.trace/` with local execution traces for debugging

`result.json` is not just the final report. It is a run manifest that includes the generated documents and summary counters.

## Notes

- Chain aliases such as `bsc`, `eth`, `arb`, `op`, `base`, `scroll`, and `linea` are supported.
- If a chain alias is unknown, the pipeline resolves the chain from the Li.Fi chain map during the first flow.
- Local traces are generated automatically in the working directory unless tracing is disabled.

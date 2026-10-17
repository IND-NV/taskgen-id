# Context for AI-assisted development

This file is the durable project handoff for future maintainers and AI assistants. Read it together with `README.md` and the current source; the source code is authoritative when this note becomes stale.

## Project identity

- Repository: https://github.com/IND-NV/taskgen-id
- Default branch: `main`
- Product: TaskGen Indonesia, a Rust CLI + Google Colab notebook for generating Indonesian SFT-style prompts with the Google Gemini API.
- Current main files: `src/main.rs`, `Cargo.toml`, `Cargo.lock`, `taskgen_id.ipynb`, `README.md`.
- Runtime: Rust edition 2024; CLI binary/package name is `taskgen`.
- The Colab notebook clones this repository's `main` branch, builds the Rust binary, and stores a consolidated dataset at `MyDrive/TaskGen-Indonesia/task_id.json`.

## Current behavior

### Rust CLI

- Calls Gemini's REST `generateContent` endpoint.
- Default model: `gemini-3.5-flash-lite`; default temperature: `1.0`.
- Samples category/domain/subdomain and difficulty levels 1–10 from weighted distributions.
- Requests up to 30 prompts per API batch and processes batches concurrently according to `--workers`.
- Writes JSONL records with fields `prompt`, `domain`, `subdomain`, `difficulty`, `language`, and `model`.
- Supports `--append`, optional exact/near-duplicate removal, API key files, proxy files, token statistics, and optional cost estimates.
- Generates a dataset summary README in the parent directory of the `--output` file.

### Google Colab notebook

- File name is `taskgen_id.ipynb` (not `TaskGen_Indonesia_Colab.ipynb`).
- Uses a widget UI for model, count, difficulty, categories, workers, and deduplication.
- Fetches models from Gemini API when possible, with a fallback model ID if the list request fails.
- Reads the CLI JSONL output, then consolidates data into one JSON array in Google Drive.
- Normalizes notebook dataset records to six fields: `prompt`, `domain`, `subdomain`, `difficulty`, `language`, `model`.
- Notebook generation currently fixes temperature at `1.0`; it does not expose a temperature control.
- Notebook's dataset format differs from the CLI format: CLI = JSONL, Colab master dataset = JSON array.

## High-priority issue found during source review

**Potential destructive README overwrite:** in `src/main.rs`, after generation the program computes the README path from the parent of `args.output` and opens it with `File::create`. With default `--output output.jsonl` when run from the repository root, this resolves to `./README.md` and can overwrite the project's own README with a generated dataset report.

Recommended fix:
1. Do not write generated dataset documentation to a generic `README.md` in the output parent by default.
2. Prefer a dedicated name such as `DATASET_README.md` or `output_README.md`, or add an explicit `--readme-output` option.
3. Add a guard that refuses to overwrite a pre-existing README unless the user explicitly opts in.
4. Add a regression test for running with default output in the repository root.

Until fixed, run the CLI with `--output generated/output.jsonl` and ensure the `generated` directory exists; the generated README is then placed in `generated/README.md`.

## Other review items to validate/fix

These are code-review findings or likely edge cases, not all confirmed runtime failures. Verify with tests before changing behavior.

1. **Input validation:** `parse_distribution` and `parse_difficulty` check that weights sum near 1.0 but should also reject negative, non-finite, and zero-total weights and reject unknown category IDs before sampling. Current sampling uses `WeightedIndex::new(...).unwrap()`, which can panic for invalid weights.
2. **Numeric CLI validation:** validate `--workers > 0`, a sensible `--dedup-threshold` range (normally 0.0–1.0), finite/nonnegative temperature, and nonnegative finite prices/budget.
3. **Budget race/overshoot:** the budget check occurs before concurrent batches and token totals are updated after API calls, so multiple in-flight batches may exceed the requested budget. Clarify that `--budget` is approximate or implement reservation/serialized accounting.
4. **HTTP/API robustness:** handle Gemini responses with no candidate due to safety blocking or finish reason; retry only transient failures and consider bounded retries/backoff for selected 5xx errors. Avoid logging sensitive API response bodies if they could include private data.
5. **Output integrity:** test interrupted runs, write failures, `--append`, malformed existing JSONL, and dedup behavior. Current CLI exact/semantic dedup reads the entire output into memory and compares trigram sets pairwise, which can become expensive for large datasets.
6. **Testing and CI:** there is no visible test directory or CI workflow in the repository root. Add unit tests for parsing/validation, normalization, JSONL serialization, API response parsing, and dedup; add `cargo fmt --check` and `cargo test` in GitHub Actions.
7. **Separation of concerns:** `src/main.rs` is a large single file containing domains, CLI parsing, API calls, generation, dedup, and README generation. Consider splitting into modules after behavior is covered by tests.
8. **Notebook reliability:** verify the notebook's fallback model remains available; pin the source branch or commit for reproducibility if desired; handle API model-list errors clearly; keep generated datasets and secrets out of the repository.

## Data/schema invariants to preserve

- Generated prompts should be Indonesian (`language = "id"`), while technical names may remain in their original language.
- The generator produces prompts/tasks, not answers.
- Category IDs: `math`, `coding`, `science`, `cs`, `creative`, `conversation`.
- Difficulty is an integer from 1 through 10.
- CLI output is JSONL. Notebook's master file is a JSON array.
- Do not silently discard existing dataset records during notebook writes or schema migrations.
- Never place API keys or credentials in source, notebook outputs, documentation, commits, or generated artifacts.

## Suggested next steps

1. Fix the generated README path collision first.
2. Add input validation and regression tests.
3. Add CI for formatting and tests.
4. Keep README examples, notebook path, model defaults, and data schemas aligned with the implementation.
5. Update this file whenever architecture, schema, or important behavior changes.

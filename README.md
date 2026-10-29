# TaskGen-ID

TaskGen-ID generates synthetic Indonesian questions for SFT (Supervised Fine-Tuning) datasets. It samples a category, domain, subdomain, and difficulty level, then asks a Gemini-compatible chat-completions endpoint to produce the questions.

## Current behavior

- Indonesian-only generation.
- Each API request generates a batch of **up to 2 questions**.
- `--count` controls the total number of questions to add in a run; without retries, the number of successful API requests is `ceil(count / 2)`. For example, 5 questions normally require 3 successful requests.
- `--workers` controls how many batches may be processed concurrently.
- Each worker waits 3 seconds after an API attempt. If a rate limit (HTTP 429) is returned, the request is retried up to 4 times, with a 3-second wait between attempts, then generation stops if the limit persists. Different workers can still make requests concurrently.
- Results are stored in a JSON array. New tasks are added to the existing array, and IDs continue from the number of existing records.
- The JSON array is rewritten after each completed record, so completed output is retained if a run is interrupted.
- A run report is written next to the output file as `<output-stem>_README.md`.

## Google Colab (recommended for phone users)

1. Open [TaskGen-ID-Colab.ipynb](./TaskGen-ID-Colab.ipynb) in Google Colab.
2. In Colab's **Secrets** panel, create `GEMINI_API_KEY` and enable notebook access.
3. Run the cells from top to bottom.
4. Find the output in Google Drive at `MyDrive/taskgen-id/outputs/`.

The notebook reads the API key from Colab Secrets. The key is not stored in the notebook or printed in logs. Gemini API use remains subject to the account's quota and Google AI Studio terms.

The notebook defaults to `COUNT = 5` and `WORKERS = 1` for a small first test. Increase them when ready. If an existing output file contains records from the old schema, choose a new `OUTPUT_NAME` to avoid mixing old and new record formats.

## Output format

The output is a **JSON array** containing task objects. Each object uses these seven fields in this order:

| Field | Meaning |
|---|---|
| `question` | Generated question text |
| `language` | Always `"Indonesia"` |
| `main_category` | Broad category, such as `math`, `coding`, or `science` |
| `domain` | Domain name, such as `Algebra` |
| `subdomain` | More specific topic, such as `polynomials` |
| `difficulty_level` | Difficulty from 1 to 10 |
| `id` | Sequential six-digit string, such as `"000001"` |

Example:

```json
{
  "question": "Jika 2x + 5 = 15, berapakah nilai x?",
  "language": "Indonesia",
  "main_category": "math",
  "domain": "Algebra",
  "subdomain": "linear_equations",
  "difficulty_level": 2,
  "id": "000001"
}
```

In the actual `.json` file, all task objects are contained in one array.

## CLI options

Build the Rust program with:

```bash
cargo build --release
```

Common options:

| Option | Default | Meaning |
|---|---|---|
| `--api-key` | `GEMINI_API_KEY` environment variable | Gemini API key |
| `--api-base` | Gemini OpenAI-compatible endpoint | API base URL |
| `-m, --model` | `gemini-3.8-flash` | Model name |
| `-c, --count` | `250` | Number of questions to add |
| `-w, --workers` | `5` | Concurrent batch workers |
| `-o, --output` | `output.json` | Output JSON array path |
| `-t, --temperature` | `0.9` | Sampling temperature |
| `--distribution` | Built-in balanced distribution | Category weights |
| `--difficulty` | Built-in difficulty distribution | Difficulty weights |
| `--system-prompt` | Built-in prompt | Override generation instructions |
| `--dedup` | Off | Run deduplication after generation |
| `--dedup-threshold` | `0.6` | Similarity threshold for semantic deduplication |
| `--input-price`, `--output-price` | Not set | Token prices per million tokens for cost estimates |
| `--budget` | Not set | Approximate USD budget cap; requires both price options |

The CLI also contains optional proxy, API-key rotation, and free-model discovery settings. These are not used by the Google Colab notebook.

## Categories and difficulty

The generator samples from these broad categories:

- `math`: algebra, calculus, probability, statistics, geometry, and related topics
- `coding`: Python, Rust, JavaScript, C/C++, SQL, web development, and other programming topics
- `science`: physics, chemistry, biology, earth science, astronomy
- `cs`: algorithms, data structures, operating systems, networking, databases, machine learning, and related topics
- `creative`: fiction, poetry, screenwriting, journalism, songwriting, and other writing tasks
- `conversation`: debate, advice, interviews, teaching, roleplay, and related topics

Difficulty levels range from **1 (very easy)** to **10 (expert / highly advanced)**. Difficulty affects both the phrasing and the complexity of the generated question.

## Error handling

- **Rate limits (HTTP 429):** up to 4 retries, waiting 3 seconds between attempts; stops if the rate limit persists.
- **Timeouts:** retries with backoff; 5 consecutive timeouts trigger graceful shutdown.
- **Billing errors:** stop generation gracefully.
- **Output writes:** the JSON array is saved after each completed record.

## Important note about appending

Each run adds tasks to the JSON array in the chosen output file and continues IDs based on the number of records already in that file. For example, if the file contains 20 records and you request 20 more, the intended total is 40 records. To start a separate dataset, use a different output filename.

# pdip examples

Runnable mini-apps that demonstrate a slice of pdip end-to-end. Each
example is small enough to read in one sitting and can be booted with
a single command against the checked-out source tree.

| Example | What it shows | Run |
|---|---|---|
| [`crud_api/`](./crud_api) | Minimal REST + CQRS + Repository app. One `Note` entity, a `CreateNote` command, a `ListNotes` query, and a Flask-Restx resource that dispatches both. Persists to a local SQLite file via pdip's `RepositoryProvider`. | `python examples/crud_api/main.py` |
| [`etl/`](./etl) | Minimal ETL flow: two SQLite databases (source / target) over pdip's `InMemoryProvider`. Seeds three rows, copies them across, prints what landed. Demonstrates the cross-adapter `execute` / `execute_many` / `fetch_query` primitives without booting an external database. | `python examples/etl/main.py` |
| [`pubsub_observer/`](./pubsub_observer) | Minimal observer pattern over `MessageBroker.subscribe`. Two callbacks register against two different events; the script publishes one of each and prints what each observer saw. Skips the multi-process worker pipeline so the demo boots in milliseconds. | `python examples/pubsub_observer/main.py` |

## Running an example

From the repo root after `pip install -e ".[api]"` (or
`pip install -e ".[api,integrator]"` if the example needs it):

```bash
python examples/<name>/main.py
```

Each example's own `README.md` documents its endpoints / CLI and the
concrete curl / flow you can exercise after boot.

## Why these live in the repo

The `README.md` snippets in the repo root are illustrative but not
runnable — they elide the DI wiring, the config file, and the imports.
These examples fill the gap: you can read them, copy from them, and
they stay in sync with the framework because CI type-checks their
imports as part of the release build.

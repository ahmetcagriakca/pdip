# examples/crud_api — minimal CQRS + REST with pdip

A self-contained "notes" service that shows how a pdip app is wired
end-to-end: entry point, DI container, CQRS dispatcher, SQLAlchemy
repository, Flask-Restx resource. Reading order is roughly
`main.py` → `domain/note/Note.py` → the two CQRS slices under
`application/` → `application/controllers/NotesResource.py`.

## What the example intentionally skips

- **No authentication / tenancy**: pdip's `Entity` carries audit and
  tenant columns automatically; this example uses the defaults so the
  CQRS flow is the focus, not the row-level access story.
- **No migrations**: SQLAlchemy's `metadata.create_all()` is called at
  boot for simplicity. Real apps use Alembic or pdip's seed-runner.
- **No validation layer** beyond what `@requestclass` gives you; a
  production app would add one.

## Boot

From the repo root, with the `[api]` extra installed:

```bash
pip install -e ".[api]"     # pulls Flask, Flask-Restx, Flask-Injector, Werkzeug
cd examples/crud_api
python main.py
```

The app starts on `http://127.0.0.1:5000`. Hit Ctrl-C to stop.

On first boot `application.yml` points `DATABASE.HOST` at
`notes.db`; SQLite creates the file next to `main.py` and
`metadata.create_all()` provisions the `Note` table.

## Exercise it

```bash
# Create a note
curl -s -X POST http://127.0.0.1:5000/api/Application/Notes \
     -H "Content-Type: application/json" \
     -d '{"Title": "Buy milk", "Body": "2 %"}'

# List notes — returns the freshest 50 ordered by CreateUserTime DESC
curl -s http://127.0.0.1:5000/api/Application/Notes | python -m json.tool
```

Expected `GET` response shape (trimmed):

```json
{
  "IsSuccess": true,
  "Result": {
    "Data": [
      {"Id": "...", "Title": "Buy milk", "Body": "2 %", "CreateUserTime": "..."}
    ]
  }
}
```

`CreateUserTime` (and `UpdateUserTime`, `CreateUserId`, `UpdateUserId`,
`TenantId`, `GcRecId`) come from pdip's `Entity` base class — see
[ADR-0010](../../docs/governance/adr/0010-audit-columns-on-base-entity.md)
and [ADR-0011](../../docs/governance/adr/0011-multi-tenancy-via-tenant-id.md)
for the rationale.

## Where to look for each pdip primitive

| Concept | File |
|---|---|
| `Pdi` boot + DI container + auto-discovery | [`main.py`](main.py) |
| Command (intent to change state) + handler | [`application/CreateNote/`](application/CreateNote/) |
| Query (read-only) + handler + DTO + response | [`application/ListNotes/`](application/ListNotes/) |
| REST resource that dispatches both | [`application/controllers/NotesResource.py`](application/controllers/NotesResource.py) |
| SQLAlchemy entity on top of pdip's `Entity` / `EntityBase` | [`domain/note/Note.py`](domain/note/Note.py) |
| YAML config + env-overrides | [`application.yml`](application.yml), [ADR-0005](../../docs/governance/adr/0005-yaml-configuration-with-env-overrides.md) |

## Extending the pattern

- Add a second command (e.g. `DeleteNote`) and handler — the
  `Dispatcher` picks it up automatically via the auto-discovery
  described in [ADR-0015](../../docs/governance/adr/0015-service-auto-discovery.md).
- Add a query parameter (e.g. text search). Follow the
  "Request → Query → Specification → Response" shape already used in
  [`ListNotes/`](application/ListNotes/).
- Swap SQLite for PostgreSQL by changing `application.yml`'s
  `DATABASE` block — the code is unchanged.

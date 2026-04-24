# ADR-0005: Load configuration from YAML with environment variable overrides

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** configuration

## Context

pdip runs in local development, CI, and production. The same codebase
needs different database connection strings, log levels, API ports, and
secret material across these environments. We want a single mechanism
that is readable for humans, safe in source control, and ergonomic for
containerised deployments where secrets come from the environment.

## Decision

Configuration is layered:

1. **Base file:** `application.yml` at the project root holds defaults.
2. **Environment overlay:** `application.{ENVIRONMENT}.yml` (for example
   `application.production.yml`) overlays the base file when the
   `ENVIRONMENT` variable is set.
3. **Environment variable override:** individual keys can be overridden
   with `{CONFIG_CLASS}_{PROPERTY}=value`, which always wins.

The `ConfigManager` in `pdip/configuration/config_manager.py` discovers
all subclasses of `BaseConfig` (`pdip/configuration/models/base/base_config.py`),
loads the YAML layers, maps `CamelCase` YAML keys to `snake_case`
attributes, and applies environment overrides last. Each fully populated
config instance is registered as a singleton in the DI container so
consumers inject `ApplicationConfig`, `DatabaseConfig`, `ApiConfig`, and
friends directly.

## Consequences

### Positive

- The base file documents every tunable; newcomers learn the surface by
  reading one file.
- Secrets do not have to live in YAML; environment variables override
  defaults at runtime, which fits the Twelve-Factor model.
- Config objects are strongly typed, injected, and testable.

### Negative

- The CamelCase-to-snake_case mapping is a small piece of magic that
  must be learned.
- Misspelled YAML keys silently fall through to defaults unless the
  config class validates them. Contributors are expected to add
  validation in the config class when a field is required.

### Neutral

- The `ENVIRONMENT` variable becomes a load-bearing environment variable
  for pdip deployments. It is documented in the application config.

## Alternatives considered

### Option A — Pure environment variables

- **Pro:** Perfect fit for containers; no file I/O.
- **Con:** No structured grouping; dozens of `PDIP_*` variables become
  unreadable.
- **Why rejected:** YAML gives us structure without giving up env
  overrides.

### Option B — JSON or TOML

- **Pro:** JSON is ubiquitous; TOML has good tool support.
- **Con:** JSON lacks comments; TOML's nested structure is awkward for
  per-environment overlays.
- **Why rejected:** YAML's readability and overlay ergonomics win.

### Option C — Python files as config

- **Pro:** Full Python power in configuration.
- **Con:** Configuration becomes code: executable at load time and hard
  to validate or audit.
- **Why rejected:** Configuration should be data, not code.

## Follow-ups

- Document the override rules prominently once user-facing docs exist.
- Consider a `pdip config print` command that shows the fully resolved
  configuration for debugging.

## References

- Code: `pdip/configuration/config_manager.py`,
  `pdip/configuration/models/base/base_config.py`,
  `pdip/configuration/models/application/application_config.py`

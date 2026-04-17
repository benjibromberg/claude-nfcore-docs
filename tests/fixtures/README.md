# Pipeline Test Fixtures

Pinned nf-core pipeline versions used as realistic environments for E2E testing.
Cloned on first run by `setup.sh`, gitignored (not committed).

## Selection criteria

We chose fixtures to maximize coverage across two dimensions:

### 1. nf-core template generations

The nf-core template evolves across tools versions. Each version introduces new
conventions that the skill must handle. We pin one pipeline per major template era:

| Template era | Key features introduced | Fixture |
|--------------|------------------------|---------|
| **pre-3.0** | `lib/` groovy helpers, nf-validation plugin, no RO-Crate | fetchngs 1.12.0 |
| **3.2–3.3** | RO-Crate, nf-schema plugin (replaces nf-validation) | funcscan 3.0.0 |
| **3.5** (current) | Topic-based version reporting, strict syntax lint | rnaseq 3.24.0 |

### 2. Pipeline structural variety

| Dimension | fetchngs 1.12.0 | funcscan 3.0.0 | rnaseq 3.24.0 |
|-----------|-----------------|----------------|---------------|
| **Size** | Small (10 components) | Medium (52) | Large (101) |
| **nf-core modules** | 4 | 42 | 71 |
| **Local modules** | 6 (directory-based) | 6 (flat files) | 5 (directory-based) |
| **Subworkflows** | 5 | 4 | 25 |
| **nf-schema** | No (old nf-validation) | Yes | Yes |
| **RO-Crate** | No | Yes | Yes |
| **Topic versions** | No | No | Yes |
| **Expected lint state** | Most warnings | Some warnings | Fewest warnings |

### Why these specific versions (not latest)?

- **fetchngs 1.12.0** is the latest release but uses a pre-3.0 template — it hasn't
  synced to modern nf-core conventions yet. This is a realistic scenario (many pipelines
  lag on template syncs) and tests how the skill handles legacy patterns.

- **funcscan 3.0.0** is the latest release, using template 3.3.2. It has flat local
  modules (not directory-based) which the skill should flag as a compliance gap.

- **rnaseq 3.24.0** is the latest release on template 3.5.2 (matching our installed
  nf-core tools). It represents the current gold standard — the skill should find
  minimal issues here.

## Setup

```bash
# Clone all fixtures (runs once, ~25MB total)
./setup.sh

# Verify
ls -d fetchngs/ funcscan/ rnaseq/
```

## Adding a new fixture

1. Add an entry to `pipelines.json`
2. Add the directory name to `../../.gitignore`
3. Update this README with the selection rationale
4. Run `./setup.sh` to clone it
5. Add E2E tests in `../test_e2e.py` that use the new fixture

## Future work

- **Changelog-based eval** (#32): pin at N-2 version, compare skill findings against
  what developers fixed in N-1 and N releases
- **Snapshot testing**: record "golden" lint output and compliance reports for regression
  detection

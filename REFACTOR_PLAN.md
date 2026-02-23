# OpenViking Refactor Plan

> **Status**: In Progress  
> **Last Updated**: 2026-02-23  
> **Maintainer**: Grok Build Agent

This document tracks the ongoing refactoring efforts to improve the OpenViking codebase quality, maintainability, and developer experience.

---

## Overview

### Pain Points Addressed

| ID | Pain Point | Impact | Effort |
|----|------------|--------|--------|
| P1 | Sync wrapper duplication (SyncOpenViking, SyncHTTPClient) | High | Medium |
| P2 | Session methods duplicated in client/service | Medium | Low |
| P3 | VikingFS god-class (800+ lines) | High | High |
| P4 | `_ensure_initialized` duplication across services | Medium | Low |
| P5 | Queue status serialization duplicated | Low | Low |
| P6 | Weak type safety (`-> Any`) | High | Low |
| P7 | Two `Session` classes (confusing) | Medium | Medium |
| P8 | Global singletons (`AsyncOpenViking`) | Medium | Medium |
| P9 | Sync/async issues (run_async in async context) | High | Medium |
| P10 | Thin service layer (most logic in VikingFS) | Medium | High |

---

## Execution Order

The following order was chosen to maximize impact while minimizing risk:

1. ✅ **Step 1**: Extract queue status helper (low effort, removes duplication)
2. ✅ **Step 3**: Add return types (low effort, high impact for DX)
3. ✅ **Step 2**: Consolidate `_ensure_initialized` into base service class
4. ⏳ **Step 4**: Auto-generate sync wrappers
5. ⏳ **Step 6**: Unify the two Session classes
6. ⏳ **Step 5**: Split VikingFS into focused modules
7. ❌ **Step 7**: Add mypy strict mode (deferred - too many issues to fix at once)

---

## Completed Steps

### ✅ Step 1: Extract Queue Status Helper

**Files Modified**:
- `openviking/service/_helpers.py` (created)
- `openviking/service/resource_service.py`

**Changes**:
- Created `serialize_queue_status()` helper function
- Replaced 3 identical inline dict comprehensions in `ResourceService` with helper calls

**Tests**: `tests/misc/test_serialize_queue_status.py` (4 test cases)

**Lines**: +31 / −12

---

### ✅ Step 3: Add Return Types

**Files Modified**:
- `openviking/service/search_service.py`
- `openviking_cli/client/base.py`
- `openviking/client/local.py`
- `openviking/async_client.py`
- `openviking/sync_client.py`
- `openviking_cli/client/sync_http.py`

**Changes**:
| Method | Before | After |
|--------|--------|-------|
| `SearchService.search()` | `-> Any` | `-> FindResult` |
| `SearchService.find()` | `-> Any` | `-> FindResult` |
| `BaseClient.find()` | untyped | `-> FindResult` |
| `BaseClient.search()` | untyped | `-> FindResult` |
| `BaseClient.get_status()` | untyped | `-> Union[Any, Dict[str, Any]]` |
| `LocalClient.find()` | `-> Any` | `-> FindResult` |
| `LocalClient.search()` | `-> Any` | `-> FindResult` |
| `LocalClient.session()` | `-> Any` | `-> FullSession` |
| `LocalClient.get_status()` | `-> Any` | `-> SystemStatus` |
| `LocalClient.observer` | `-> Any` | `-> ObserverService` |
| `AsyncOpenViking.search()` | untyped | `-> FindResult` |
| `AsyncOpenViking.find()` | untyped | `-> FindResult` |
| `SyncOpenViking.search()` | untyped | `-> FindResult` |
| `SyncOpenViking.find()` | untyped | `-> FindResult` |
| `SyncOpenViking.get_status()` | untyped | `-> Union[SystemStatus, Dict[str, Any]]` |
| `SyncHTTPClient.search()` | untyped | `-> FindResult` |
| `SyncHTTPClient.find()` | untyped | `-> FindResult` |

**Pattern Used**:
- `from __future__ import annotations` for deferred type evaluation
- `TYPE_CHECKING` guard to avoid circular imports at runtime

**Lines**: +52 / −27

---

### ✅ Step 2: Refactor Base Service Class

**Files Modified**:
- `openviking/service/_helpers.py` (extended)
- `openviking/service/__init__.py`
- `openviking/service/fs_service.py`
- `openviking/service/search_service.py`
- `openviking/service/relation_service.py`
- `openviking/service/pack_service.py`

**Changes**:
- Created `VikingFSService` base class with shared:
  - `__init__(self, viking_fs: Optional[VikingFS] = None)`
  - `set_viking_fs(self, viking_fs: VikingFS) -> None`
  - `_ensure_initialized(self) -> VikingFS`
- Refactored 4 services to extend `VikingFSService`:
  - `FSService`
  - `SearchService`
  - `RelationService`
  - `PackService`

**Intentionally NOT Changed**:
- `SessionService` — has multi-dependency guard (`viking_fs`, `vikingdb`, `session_compressor`)
- `ResourceService` — has multi-dependency guard (`resource_processor`, `skill_processor`, `viking_fs`)
- `OpenVikingService` (core) — checks `_initialized` flag, different pattern

**Tests**: `tests/misc/test_viking_fs_service.py` (9 test cases)

**Lines**: +40 / −68

---

## Pending Steps

### ⏳ Step 4: Auto-Generate Sync Wrappers

**Goal**: Eliminate manual sync wrapper duplication

**Current State**:
- `SyncOpenViking` manually wraps ~30 methods
- `SyncHTTPClient` manually wraps ~25 methods
- Pattern is identical: `return run_async(self._async_client.method(...))`

**Proposed Solution**:
Create a decorator or metaclass that auto-generates sync versions:

```python
@sync_wrapper
class SyncOpenViking:
    def __init__(self, async_client: AsyncOpenViking):
        self._async = async_client
```

**Effort**: Medium
**Impact**: High (removes ~100 lines of boilerplate per class)

---

### ⏳ Step 6: Unify the Two Session Classes

**Goal**: Eliminate confusion between `openviking.session.Session` and `openviking.client.session.Session`

**Current State**:
- `openviking/session/session.py` — Full Session (used by LocalClient)
- `openviking/client/session.py` — Proxy Session (used by HTTP clients)
- Both have similar APIs but different implementations

**Proposed Solution**:
Create a `BaseSession` protocol/interface that both implement, or merge into a single class with a transport abstraction.

**Effort**: Medium
**Impact**: Medium (reduces developer confusion)

---

### ⏳ Step 5: Split VikingFS God Class

**Goal**: Break 800+ line `VikingFS` into focused modules

**Current State**:
- `openviking/storage/viking_fs.py` ~800 lines
- Handles: file operations, search, indexing, relations, caching

**Proposed Structure**:
```
openviking/storage/viking_fs/
├── __init__.py          # VikingFS facade
├── _base.py             # Core filesystem operations
├── _search.py           # Semantic search operations
├── _relations.py        # Relation management
└── _cache.py            # Caching layer
```

**Effort**: High
**Impact**: High (improves maintainability, testability)

---

### ❌ Step 7: Mypy Strict Mode (Deferred)

**Goal**: Enable `strict = true` in pyproject.toml

**Current State**:
- ~200+ type errors when strict mode is enabled
- Many missing annotations in parser/extraction modules

**Decision**: Deferred until after other refactors stabilize the API surface.

---

## New Dependencies Introduced

| Dependency | Purpose | Location |
|------------|---------|----------|
| None | — | — |

All refactors use existing patterns (`from __future__ import annotations`, `TYPE_CHECKING`).

---

## Decoupling Achieved

| Before | After | Benefit |
|--------|-------|---------|
| 4 services duplicated VikingFS init logic | 4 services extend `VikingFSService` | Single source of truth |
| Queue status serialization inline (3×) | `serialize_queue_status()` helper | Reusable, testable |
| `-> Any` on core API methods | `-> FindResult`, `-> SystemStatus` | Better IDE support, fewer bugs |

---

## How to Pick Up Where You Left Off

1. **Review this plan** to understand completed vs pending work
2. **Check git status**: `git status` and `git diff HEAD` to see current changes
3. **Run tests**: `pytest tests/misc/ -v` to verify existing refactors
4. **Choose next step**: Pick from the ⏳ Pending Steps section above
5. **Follow the pattern**: Each step should be small, reviewable, and preserve behavior

---

## Architecture Documentation Updates Needed

The following docs should be updated to reflect the new structure:

- [ ] `docs/en/concepts/01-architecture.md` — Add Service Layer base class note
- [ ] `docs/en/concepts/05-storage.md` — Document VikingFSService pattern
- [ ] `README.md` — Update Project Architecture section if needed
- [ ] Add `VikingFSService` to API reference docs

---

## Testing Strategy

Each completed step includes tests:

```bash
# Run all refactor-related tests
pytest tests/misc/test_serialize_queue_status.py -v
pytest tests/misc/test_viking_fs_service.py -v

# Run full test suite (requires full environment)
pytest tests/ -v --cov=openviking
```

---

## Rollback Plan

If issues arise, each step can be rolled back independently:

```bash
# Rollback Step 2 (base service)
git checkout HEAD -- openviking/service/fs_service.py
# ... etc for each file

# Rollback Step 3 (return types)
git checkout HEAD -- openviking/service/search_service.py
# ... etc for each file

# Rollback Step 1 (queue helper)
git checkout HEAD -- openviking/service/_helpers.py
```

---

## Questions or Issues?

- Check existing tests in `tests/misc/`
- Review the git diff for each completed step
- Ensure new code follows the `from __future__ import annotations` + `TYPE_CHECKING` pattern
- Keep changes small and reviewable

---

*This document is a living plan. Update it as new pain points are discovered or priorities shift.*

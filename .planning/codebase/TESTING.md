# Testing Patterns

**Analysis Date:** 2026-02-04

## Test Framework

**Runner:**
- None detected
- No pytest.ini, pytest.toml, jest.config.js, or vitest.config.ts found
- No test files in codebase (no `test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts`)

**Assertion Library:**
- Not applicable (no tests present)

**Run Commands:**
```bash
# No test commands configured in package.json or standard Python test runners
```

## Test File Organization

**Location:**
- No test files detected in the project

**Naming:**
- Not established (no existing test files to analyze)

**Structure:**
```
# No test directory structure present
```

## Test Structure

**Suite Organization:**
Not applicable - no tests exist in the codebase.

**Expected Pattern (based on project structure):**
```python
# Python tests would likely use pytest with async support
import pytest
from quart import Quart

@pytest.mark.asyncio
async def test_endpoint():
    # Test Quart async endpoints
    pass
```

**TypeScript Pattern (if implemented):**
```typescript
// Would likely use Vitest (matches Rsbuild ecosystem)
import { describe, it, expect } from 'vitest';

describe('conversationService', () => {
  it('should fetch conversations', async () => {
    // Test API service methods
  });
});
```

## Mocking

**Framework:**
- Not established (no tests present)

**Likely Approach:**
- Python: `pytest-mock` or `unittest.mock` for services/API calls
- TypeScript: Vitest mocking utilities

**What to Mock:**
- External API calls (YNAB, Mealie, Paperless-NGX, Tavily)
- LLM interactions (OpenAI/llama-server)
- Database queries (Tortoise ORM)
- Authentication/JWT verification

**What NOT to Mock:**
- Business logic functions (these should be tested directly)
- Data transformations
- Utility functions without side effects

## Fixtures and Factories

**Test Data:**
Not established - would need fixtures for:
- User objects with various authentication states
- Conversation and Message objects
- Mock YNAB/Mealie API responses
- Mock ChromaDB query results

**Expected Pattern:**
```python
# Python fixtures with pytest
@pytest.fixture
async def test_user():
    """Create a test user."""
    user = await User.create(
        username="testuser",
        email="test@example.com",
        auth_provider="local"
    )
    yield user
    await user.delete()

@pytest.fixture
def mock_ynab_response():
    """Mock YNAB API budget response."""
    return {
        "budget_name": "Test Budget",
        "to_be_budgeted": 100.00,
        "total_budgeted": 2000.00,
    }
```

## Coverage

**Requirements:**
- No coverage requirements configured
- No `.coveragerc` or coverage configuration in `pyproject.toml`

**Current State:**
- **0% test coverage** (no tests exist)

**View Coverage:**
```bash
# Would use pytest-cov for Python
pytest --cov=. --cov-report=html

# Would use Vitest coverage for TypeScript
npx vitest --coverage
```

## Test Types

**Unit Tests:**
- Not present
- Should test: Service methods, utility functions, data transformations, business logic

**Integration Tests:**
- Not present
- Should test: API endpoints, database operations, authentication flows, external service integrations

**E2E Tests:**
- Not present
- Could use: Playwright or Cypress for frontend testing

## Common Patterns

**Async Testing:**
Expected pattern for Quart/async Python:
```python
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_query_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/conversation/query",
            json={"query": "test", "conversation_id": "uuid"}
        )
        assert response.status_code == 200
```

**Error Testing:**
Expected pattern:
```python
@pytest.mark.asyncio
async def test_unauthorized_access():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/conversation/query")
        assert response.status_code == 401
        assert "error" in response.json()
```

## Testing Gaps

**Critical Areas Without Tests:**

1. **Authentication & Authorization:**
   - OIDC flow (`blueprints/users/__init__.py` - 188 lines)
   - JWT token refresh
   - Admin authorization decorator
   - PKCE verification

2. **Core RAG Functionality:**
   - Document indexing (`main.py` - 274 lines)
   - Vector store queries (`blueprints/rag/logic.py`)
   - LLM agent tools (`blueprints/conversation/agents.py` - 733 lines)
   - Query classification

3. **External Service Integrations:**
   - YNAB API client (`utils/ynab_service.py` - 576 lines)
   - Mealie API client (`utils/mealie_service.py` - 477 lines)
   - Paperless-NGX API client (`utils/request.py`)
   - Tavily web search

4. **Streaming Responses:**
   - Server-Sent Events in `/api/conversation/query`
   - Frontend SSE parsing (`conversationService.sendQueryStream()`)

5. **Database Operations:**
   - Conversation creation and retrieval
   - Message persistence
   - User CRUD operations

6. **Frontend Components:**
   - ChatScreen streaming state (`ChatScreen.tsx` - 386 lines)
   - Message bubbles rendering
   - Authentication context

## Recommended Testing Strategy

**Phase 1: Critical Path Tests**
- Authentication endpoints (login, callback, token refresh)
- Conversation query endpoint (non-streaming)
- User creation and retrieval
- Basic YNAB/Mealie service methods

**Phase 2: Integration Tests**
- Full OIDC authentication flow
- Conversation with messages persistence
- RAG document indexing and retrieval
- External API error handling

**Phase 3: Frontend Tests**
- Component rendering tests
- API service method tests
- Streaming response handling
- Authentication state management

**Phase 4: E2E Tests**
- Complete user journey (login → query → response)
- Conversation management
- Admin operations

## Testing Dependencies to Add

**Python:**
```toml
# Add to pyproject.toml [tool.poetry.group.dev.dependencies] or requirements-dev.txt
pytest = "^7.0"
pytest-asyncio = "^0.21"
pytest-cov = "^4.0"
pytest-mock = "^3.10"
httpx = "^0.24"  # For testing async HTTP
```

**TypeScript:**
```json
// Add to raggr-frontend/package.json devDependencies
"@vitest/ui": "^1.0.0",
"vitest": "^1.0.0",
"@testing-library/react": "^14.0.0",
"@testing-library/jest-dom": "^6.0.0"
```

## Testing Best Practices (Not Yet Implemented)

**Database Tests:**
- Use separate test database
- Reset database state between tests
- Use Aerich to apply migrations in test environment

**Async Tests:**
- Mark all async tests with `@pytest.mark.asyncio`
- Use `AsyncClient` for Quart endpoint testing
- Properly await all async operations

**Mocking External Services:**
- Mock all HTTP calls to external APIs
- Use `httpx.MockTransport` or `responses` library
- Return realistic mock data based on actual API responses

**Frontend Testing:**
- Mock API services in component tests
- Test loading/error states
- Test user interactions (clicks, form submissions)
- Verify SSE stream handling

---

*Testing analysis: 2026-02-04*

**CRITICAL NOTE:** This codebase currently has **no automated tests**. All functionality relies on manual testing. Implementing a test suite should be a high priority, especially for:
- Authentication flows (security-critical)
- External API integrations (reliability-critical)
- Database operations (data integrity-critical)
- Streaming responses (complexity-critical)

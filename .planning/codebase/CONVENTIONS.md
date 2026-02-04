# Coding Conventions

**Analysis Date:** 2026-02-04

## Naming Patterns

**Files:**
- Python: `snake_case.py` - `ynab_service.py`, `mealie_service.py`, `oidc_service.py`
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for services
  - Components: `ChatScreen.tsx`, `AnswerBubble.tsx`, `QuestionBubble.tsx`
  - Services: `conversationService.ts`, `userService.ts`, `oidcService.ts`
- Config files: `snake_case.py` - `aerich_config.py`, `oidc_config.py`

**Functions:**
- Python: `snake_case` - `get_budget_summary()`, `parse_relative_date()`, `consult_simba_oracle()`
- TypeScript: `camelCase` - `handleQuestionSubmit()`, `sendQueryStream()`, `fetchWithRefreshToken()`

**Variables:**
- Python: `snake_case` - `budget_id`, `access_token`, `llama_url`, `current_user_uuid`
- TypeScript: `camelCase` - `conversationId`, `streamingContent`, `isLoading`

**Types:**
- Python classes: `PascalCase` - `YNABService`, `MealieService`, `LLMClient`, `User`, `Conversation`
- Python enums: `PascalCase` with SCREAMING_SNAKE_CASE values - `Speaker.USER`, `Speaker.SIMBA`
- TypeScript interfaces: `PascalCase` - `Message`, `Conversation`, `QueryResponse`, `StreamEvent`
- TypeScript types: `PascalCase` - `ChatScreenProps`, `QuestionAnswer`

**Constants:**
- Python: `SCREAMING_SNAKE_CASE` - `DATABASE_URL`, `TORTOISE_CONFIG`, `PROVIDER`
- TypeScript: `camelCase` - `baseUrl`, `conversationBaseUrl`

## Code Style

**Formatting:**
- Python: No explicit formatter configured (no Black, autopep8, or yapf config detected)
- Manual formatting observed: 4-space indentation, line length ~88-100 chars
- TypeScript: Biome 2.3.10 configured in `raggr-frontend/package.json`
  - No explicit biome.json found, using defaults

**Linting:**
- Python: No linter config detected (no pylint, flake8, ruff config)
- TypeScript: Biome handles linting via `@biomejs/biome` package

**Imports:**
- Python: Standard library first, then third-party, then local imports
  ```python
  import os
  import logging
  from datetime import datetime

  from dotenv import load_dotenv
  from quart import Blueprint

  from .models import User
  from .logic import get_conversation
  ```
- TypeScript: React imports, then third-party, then local (relative)
  ```typescript
  import { useEffect, useState } from "react";
  import { conversationService } from "../api/conversationService";
  import { QuestionBubble } from "./QuestionBubble";
  ```

## Import Organization

**Order:**
1. Standard library imports
2. Third-party framework imports (Flask/Quart/React/etc)
3. Local application imports (blueprints, utils, models)

**Path Aliases:**
- None detected in TypeScript - uses relative imports (`../api/`, `./components/`)
- Python uses absolute imports for blueprints and utils modules

**Absolute vs Relative:**
- Python: Absolute imports for cross-module (`from utils.ynab_service import YNABService`)
- TypeScript: Relative imports (`../api/conversationService`)

## Error Handling

**Patterns:**
- Python: Try/except with detailed logging
  ```python
  try:
      # operation
      logger.info("[SERVICE] Operation details")
  except httpx.HTTPStatusError as e:
      logger.error(f"[SERVICE] HTTP error: {e.response.status_code}")
      raise
  except Exception as e:
      logger.error(f"[SERVICE] Error: {type(e).__name__}: {str(e)}")
      logger.exception("[SERVICE] Full traceback:")
      raise
  ```
- TypeScript: Try/catch with console.error, re-throw or handle gracefully
  ```typescript
  try {
      const response = await fetch();
  } catch (error) {
      console.error("Failed to fetch:", error);
      if (error.message.includes("Session expired")) {
          setAuthenticated(false);
      }
  }
  ```

**Async Error Handling:**
- Python: `async def` functions use try/except blocks
- TypeScript: `async` functions use try/catch blocks
- Both propagate errors upward with `raise` (Python) or `throw` (TypeScript)

**HTTP Errors:**
- Python Quart: Return `jsonify({"error": "message"}), status_code`
- Python httpx: Raise HTTPStatusError, log response text
- TypeScript: Throw Error with descriptive message

## Logging

**Framework:**
- Python: Standard `logging` module
- TypeScript: `console.log()`, `console.error()`

**Patterns:**
- Python: Structured logging with prefixes
  ```python
  logger = logging.getLogger(__name__)
  logger.info("[SERVICE] Operation started")
  logger.error(f"[SERVICE] Error: {details}")
  logger.exception("[SERVICE] Full traceback:")  # After except
  ```
- Logging levels: INFO for operations, ERROR for failures, DEBUG for detailed data
- Service-specific prefixes: `[YNAB]`, `[MEALIE]`, `[YNAB TOOLS]`

**When to Log:**
- Entry/exit of major operations (API calls, database queries)
- Error conditions with full context
- Configuration/initialization status
- Performance metrics (timing critical operations)

**Examples from codebase:**
```python
logger.info(f"[YNAB] get_budget_summary() called for budget_id: {self.budget_id}")
logger.info(f"[YNAB] Total budgeted: ${total_budgeted:.2f}")
logger.error(f"[YNAB] Error in get_budget_summary(): {type(e).__name__}: {str(e)}")
```

## Comments

**When to Comment:**
- Complex business logic (date parsing, budget calculations)
- Non-obvious workarounds or API quirks
- Important configuration decisions
- Docstrings for all public functions/methods

**JSDoc/TSDoc:**
- Python: Docstrings with Args/Returns sections
  ```python
  def get_transactions(self, start_date: Optional[str] = None) -> dict[str, Any]:
      """Get transactions filtered by date range.

      Args:
          start_date: Start date in YYYY-MM-DD or relative ('this_month')

      Returns:
          Dictionary containing matching transactions and summary.
      """
  ```
- TypeScript: Inline comments, no formal JSDoc detected
  ```typescript
  // Stream events back to client as they happen
  async function generate() {
      // ...
  }
  ```

**Comment Style:**
- Python: `# Single line` or `"""Docstring"""`
- TypeScript: `// Single line` or `/* Multi-line */`
- No TODOs/FIXMEs in project code (only in node_modules)

## Function Design

**Size:**
- Python: 20-100 lines typical, some reach 150+ (service methods with error handling)
- TypeScript: 10-50 lines for React components, 20-80 for service methods
- Large functions acceptable when handling complex workflows (streaming, API interactions)

**Parameters:**
- Python: Explicit typing with `Optional[type]`, defaults for optional params
  ```python
  def get_transactions(
      self,
      start_date: Optional[str] = None,
      end_date: Optional[str] = None,
      limit: int = 50,
  ) -> dict[str, Any]:
  ```
- TypeScript: Interfaces for complex parameter objects
  ```typescript
  async sendQueryStream(
      query: string,
      conversation_id: string,
      callbacks: StreamCallbacks,
      signal?: AbortSignal,
  ): Promise<void>
  ```

**Return Values:**
- Python: Explicit return type hints - `-> dict[str, Any]`, `-> str`, `-> bool`
- TypeScript: Explicit types - `: Promise<Conversation>`, `: void`
- Dictionary/object returns for complex data (not tuples in Python)

**Async/Await:**
- Python Quart: All route handlers are `async def`
- Python services: Database queries and external API calls are `async`
- TypeScript: All API calls use `async/await` pattern

## Module Design

**Exports:**
- Python: No explicit `__all__`, classes/functions imported directly
- TypeScript: Named exports for classes/functions, default export for singleton services
  ```typescript
  export const conversationService = new ConversationService();
  ```

**Barrel Files:**
- Python: `blueprints/__init__.py` defines blueprints, re-exported
- TypeScript: No barrel files, direct imports

**Structure:**
- Python blueprints: `__init__.py` contains routes, `models.py` for ORM, `logic.py` for business logic
- Services in separate modules: `utils/ynab_service.py`, `utils/mealie_service.py`
- Separation of concerns: routes, models, business logic, utilities

## Decorators

**Authentication:**
- `@jwt_refresh_token_required` - Standard auth requirement
- `@admin_required` - Custom decorator for admin-only routes (wraps `@jwt_refresh_token_required`)

**Route Decorators:**
- `@app.route()` or `@blueprint.route()` with HTTP method
- Async routes: `async def` function signature

**Tool Decorators (LangChain):**
- `@tool` - Mark functions as LangChain tools
- `@tool(response_format="content_and_artifact")` - Specialized tool responses

**Pattern:**
```python
@conversation_blueprint.post("/query")
@jwt_refresh_token_required
async def query():
    current_user_uuid = get_jwt_identity()
    # ...
```

## Type Hints

**Python:**
- Modern type hints throughout: `dict[str, Any]`, `Optional[str]`, `list[str]`
- Tortoise ORM types: `fields.ForeignKeyRelation`
- No legacy typing module usage (using built-in generics)

**TypeScript:**
- Strict typing with interfaces
- Union types for variants: `"user" | "simba"`, `'status' | 'content' | 'done' | 'error'`
- Generic types: `Promise<T>`, `React.ChangeEvent<HTMLTextAreaElement>`

## State Management

**Python (Backend):**
- Database: Tortoise ORM async models
- In-memory: Module-level variables for services (`ynab_service`, `mealie_service`)
- Session: JWT tokens, in-memory dict for OIDC sessions (`_oidc_sessions`)

**TypeScript (Frontend):**
- React hooks: `useState`, `useEffect`, `useRef`
- localStorage for JWT tokens (via `userService`)
- No global state management library (no Redux/Zustand)

**Pattern:**
```typescript
const [isLoading, setIsLoading] = useState<boolean>(false);
const abortControllerRef = useRef<AbortController | null>(null);
```

## Database Conventions

**ORM:**
- Tortoise ORM with Aerich for migrations
- Models inherit from `Model` base class
- Field definitions: `fields.UUIDField`, `fields.CharField`, `fields.ForeignKeyField`

**Naming:**
- Table names: Lowercase plural (`users`, `conversations`, `conversation_messages`)
- Foreign keys: Singular model name (`user`, `conversation`)
- Related names: Plural (`conversations`, `messages`)

**Pattern:**
```python
class Conversation(Model):
    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=255)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User", related_name="conversations", null=True
    )

    class Meta:
        table = "conversations"
```

## API Conventions

**REST Endpoints:**
- Prefix: `/api/{resource}`
- Blueprints: `/api/user`, `/api/conversation`, `/api/rag`
- CRUD patterns: GET for fetch, POST for create/actions, PUT for update, DELETE for remove

**Request/Response:**
- JSON payloads: `await request.get_json()`
- Responses: `jsonify({...})` with optional status code
- Streaming: Server-Sent Events (SSE) with `text/event-stream` mimetype

**Authentication:**
- JWT in Authorization header (managed by `quart-jwt-extended`)
- Refresh tokens for long-lived sessions
- OIDC flow for external authentication

---

*Convention analysis: 2026-02-04*

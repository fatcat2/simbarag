# Streaming Implementation Summary

## Overview
The `/stream-query` endpoint uses Server-Sent Events (SSE) to give real-time feedback
during AI query processing: tool-execution status **and** token-by-token streaming of the
assistant's answer.

## Backend (`blueprints/conversation/__init__.py`)

### `POST /api/conversation/stream-query`
Streams SSE frames (`data: {json}\n\n`) by iterating `main_agent.astream_events(..., version="v2")`.
Event types emitted to the client:

- `tool_start` — a tool began (`{ "type": "tool_start", "tool": <name> }`), from `on_tool_start`.
- `tool_end` — a tool finished, from `on_tool_end`.
- `content` — an incremental answer chunk (`{ "type": "content", "delta": <text> }`), from
  `on_chat_model_stream`. Chunks are accumulated server-side into `streamed`.
- `response` — the final, authoritative message (`{ "type": "response", "message": <full text> }`).
  Sourced from `on_chain_end` (falling back to the accumulated `streamed` tokens). This is the
  text that is persisted to the DB via `add_message_to_conversation(..., speaker="simba")`.
- `error` — an error message.
- The stream terminates with `data: [DONE]`.

The user's message is persisted before streaming begins; the assistant message is persisted once
the stream completes.

### `POST /api/conversation/query` (legacy, non-streaming)
Backwards-compatible endpoint that returns the complete response in one JSON payload
(`{ "response": <text> }`). Kept for compatibility; the frontend uses `/stream-query`.

## Frontend

### API service (`src/api/conversationService.ts`)
- `streamQuery(query, conversation_id, onEvent, signal?, imageKey?)` — POSTs to `/stream-query`
  and drives the response through `_readSSEStream()`.
- `_readSSEStream()` — reads the `ReadableStream`, splits on `\n\n`, parses `data:` frames into
  `SSEEvent` objects, and stops on `[DONE]`.
- `SSEEvent` union: `tool_start | tool_end | content | response | error`.

### Chat state (`src/hooks/useChat.ts`)
`sendMessage()` consumes the stream and maintains a unified `messages` array:

- `tool_start` → appends a `tool` bubble (mapped to a friendly label via `TOOL_MESSAGES`) and
  resets the streaming pointer so any text after a tool call starts a fresh bubble.
- `content` → on the first delta, appends a new `simba` bubble and flips `streamingActiveRef` /
  `streaming`; subsequent deltas append to that bubble's text.
- `response` → overwrites the live `simba` bubble with the authoritative message (guaranteeing
  parity with what was persisted), or appends it if nothing streamed (e.g. an instant answer).
- `error` → surfaces a user-facing error.

A `streaming` boolean is exposed so the UI can hide the redundant loading indicator once tokens
start arriving.

### Components
- `ChatScreen.tsx` — renders `messages` (`ToolBubble` / `AnswerBubble` / `QuestionBubble`) and
  shows the standalone loading-dots `AnswerBubble` only before the first token
  (`(isLoading && !streaming) || messagesLoading`).
- `AnswerBubble.tsx` — renders the assistant message as markdown, or animated loading dots when
  `loading` is set.
- `ToolBubble.tsx` — renders tool-status messages as inline badges.

## User Experience
1. User sends a message.
2. Loading dots appear.
3. Tool status bubbles appear as tools run (e.g. "Searching Simba's records...").
4. The answer streams in word-by-word into a single assistant bubble.
5. On completion the bubble is reconciled with the persisted final text.

## Testing
```bash
# Backend
make test                       # or: .venv/bin/python -m pytest tests/

# Frontend
cd raggr-frontend && yarn build

# Full stack (manual)
docker compose up --build
```

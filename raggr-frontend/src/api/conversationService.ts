import { userService } from "./userService";

export type SSEEvent =
  | { type: "tool_start"; tool: string }
  | { type: "tool_end"; tool: string }
  | { type: "response"; message: string }
  | { type: "error"; message: string };

export type SSEEventCallback = (event: SSEEvent) => void;

interface Message {
  id: string;
  text: string;
  speaker: "user" | "simba";
  created_at: string;
}

interface Conversation {
  id: string;
  name: string;
  messages?: Message[];
  created_at: string;
  updated_at: string;
  user_id?: string;
}

interface QueryRequest {
  query: string;
}

interface QueryResponse {
  response: string;
}

interface CreateConversationRequest {
  user_id: string;
}

class ConversationService {
  private baseUrl = "/api";
  private conversationBaseUrl = "/api/conversation";

  async sendQuery(
    query: string,
    conversation_id: string,
    signal?: AbortSignal,
  ): Promise<QueryResponse> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/query`,
      {
        method: "POST",
        body: JSON.stringify({ query, conversation_id }),
        signal,
      },
    );

    if (!response.ok) {
      throw new Error("Failed to send query");
    }

    return await response.json();
  }

  async getMessages(): Promise<Conversation> {
    const response = await userService.fetchWithRefreshToken(
      `${this.baseUrl}/messages`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      throw new Error("Failed to fetch messages");
    }

    return await response.json();
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/${conversationId}`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      throw new Error("Failed to fetch conversation");
    }

    return await response.json();
  }

  async createConversation(): Promise<Conversation> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/`,
      {
        method: "POST",
      },
    );

    if (!response.ok) {
      throw new Error("Failed to create conversation");
    }

    return await response.json();
  }

  async getAllConversations(): Promise<Conversation[]> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      throw new Error("Failed to fetch conversations");
    }

    return await response.json();
  }

  async streamQuery(
    query: string,
    conversation_id: string,
    onEvent: SSEEventCallback,
    signal?: AbortSignal,
  ): Promise<void> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/stream-query`,
      {
        method: "POST",
        body: JSON.stringify({ query, conversation_id }),
        signal,
      },
    );

    if (!response.ok) {
      throw new Error("Failed to stream query");
    }

    await this._readSSEStream(response, onEvent);
  }

  private async _readSSEStream(
    response: Response,
    onEvent: SSEEventCallback,
  ): Promise<void> {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") return;
        try {
          const event = JSON.parse(data) as SSEEvent;
          onEvent(event);
        } catch {
          // ignore malformed events
        }
      }
    }
  }
}

export const conversationService = new ConversationService();

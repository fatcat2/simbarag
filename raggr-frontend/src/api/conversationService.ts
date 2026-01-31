import { userService } from "./userService";

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
  ): Promise<QueryResponse> {
    const response = await userService.fetchWithRefreshToken(
      `${this.conversationBaseUrl}/query`,
      {
        method: "POST",
        body: JSON.stringify({ query, conversation_id }),
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
}

export const conversationService = new ConversationService();

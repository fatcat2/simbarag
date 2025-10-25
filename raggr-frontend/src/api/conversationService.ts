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
  messages: Message[];
  created_at: string;
  updated_at: string;
}

interface QueryRequest {
  query: string;
}

interface QueryResponse {
  response: string;
}

class ConversationService {
  private baseUrl = "/api";

  async sendQuery(query: string): Promise<QueryResponse> {
    const response = await userService.fetchWithRefreshToken(
      `${this.baseUrl}/query`,
      {
        method: "POST",
        body: JSON.stringify({ query }),
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
}

export const conversationService = new ConversationService();

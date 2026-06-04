import { userService } from "./userService";

export interface ScheduledMessage {
  id: string;
  recipient: string;
  channel: "imessage" | "email";
  content: string;
  subject: string | null;
  scheduled_at: string;
  status: "pending" | "sent" | "failed" | "cancelled";
  recurrence: "none" | "daily" | "weekly" | "monthly";
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateScheduledMessage {
  recipient: string;
  channel: "imessage" | "email";
  content: string;
  subject?: string;
  scheduled_at: string;
  recurrence?: "none" | "daily" | "weekly" | "monthly";
}

class ScheduledMessageService {
  private baseUrl = "/api/scheduled-messages";

  async list(): Promise<ScheduledMessage[]> {
    const response = await userService.fetchWithRefreshToken(`${this.baseUrl}/`);
    if (!response.ok) throw new Error("Failed to list scheduled messages");
    return response.json();
  }

  async create(data: CreateScheduledMessage): Promise<ScheduledMessage> {
    const response = await userService.fetchWithRefreshToken(`${this.baseUrl}/`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error ?? "Failed to create scheduled message");
    }
    return response.json();
  }

  async update(id: string, data: Partial<CreateScheduledMessage> & { status?: string }): Promise<ScheduledMessage> {
    const response = await userService.fetchWithRefreshToken(`${this.baseUrl}/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error ?? "Failed to update scheduled message");
    }
    return response.json();
  }

  async remove(id: string): Promise<void> {
    const response = await userService.fetchWithRefreshToken(`${this.baseUrl}/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error ?? "Failed to delete scheduled message");
    }
  }
}

export const scheduledMessageService = new ScheduledMessageService();

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    username: string;
    email?: string;
  };
}

interface RefreshResponse {
  access_token: string;
}

class UserService {
  private baseUrl = "/api/user";

  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error("Invalid credentials");
    }

    return await response.json();
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await fetch(`${this.baseUrl}/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      // Refresh token is invalid or expired, clear storage
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      throw new Error("Failed to refresh token");
    }

    const data: RefreshResponse = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data.access_token;
  }

  async validateToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      return false;
    }

    try {
      await this.refreshToken();
      return true;
    } catch (error) {
      return false;
    }
  }

  async fetchWithAuth(
    url: string,
    options: RequestInit = {},
  ): Promise<Response> {
    const accessToken = localStorage.getItem("access_token");

    // Add authorization header
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    };

    let response = await fetch(url, { ...options, headers });

    // If unauthorized, try refreshing the token
    if (response.status === 401) {
      try {
        const newAccessToken = await this.refreshToken();

        // Retry the request with new token
        headers.Authorization = `Bearer ${newAccessToken}`;
        response = await fetch(url, { ...options, headers });
      } catch (error) {
        // Refresh failed, redirect to login or throw error
        throw new Error("Session expired. Please log in again.");
      }
    }

    return response;
  }

  async fetchWithRefreshToken(
    url: string,
    options: RequestInit = {},
  ): Promise<Response> {
    const refreshToken = localStorage.getItem("refresh_token");

    // Add authorization header
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(refreshToken && { Authorization: `Bearer ${refreshToken}` }),
    };

    let response = await fetch(url, { ...options, headers });

    // If unauthorized, try refreshing the token
    if (response.status === 401) {
      try {
        const newAccessToken = await this.refreshToken();

        // Retry the request with new token
        headers.Authorization = `Bearer ${newAccessToken}`;
        response = await fetch(url, { ...options, headers });
      } catch (error) {
        // Refresh failed, redirect to login or throw error
        throw new Error("Session expired. Please log in again.");
      }
    }

    return response;
  }

  async getMe(): Promise<{ id: string; username: string; email: string; is_admin: boolean }> {
    const response = await this.fetchWithRefreshToken(`${this.baseUrl}/me`);
    if (!response.ok) throw new Error("Failed to fetch user profile");
    return response.json();
  }

  async adminListUsers(): Promise<AdminUserRecord[]> {
    const response = await this.fetchWithRefreshToken(`${this.baseUrl}/admin/users`);
    if (!response.ok) throw new Error("Failed to list users");
    return response.json();
  }

  async adminSetWhatsapp(userId: string, number: string): Promise<AdminUserRecord> {
    const response = await this.fetchWithRefreshToken(
      `${this.baseUrl}/admin/users/${userId}/whatsapp`,
      { method: "PUT", body: JSON.stringify({ whatsapp_number: number }) },
    );
    if (response.status === 409) {
      const data = await response.json();
      throw new Error(data.error ?? "WhatsApp number already in use");
    }
    if (!response.ok) throw new Error("Failed to set WhatsApp number");
    return response.json();
  }

  async adminUnlinkWhatsapp(userId: string): Promise<void> {
    const response = await this.fetchWithRefreshToken(
      `${this.baseUrl}/admin/users/${userId}/whatsapp`,
      { method: "DELETE" },
    );
    if (!response.ok) throw new Error("Failed to unlink WhatsApp number");
  }

  async adminToggleEmail(userId: string): Promise<AdminUserRecord> {
    const response = await this.fetchWithRefreshToken(
      `${this.baseUrl}/admin/users/${userId}/email`,
      { method: "PUT" },
    );
    if (!response.ok) throw new Error("Failed to enable email");
    return response.json();
  }

  async adminDisableEmail(userId: string): Promise<void> {
    const response = await this.fetchWithRefreshToken(
      `${this.baseUrl}/admin/users/${userId}/email`,
      { method: "DELETE" },
    );
    if (!response.ok) throw new Error("Failed to disable email");
  }
}

export interface AdminUserRecord {
  id: string;
  username: string;
  email: string;
  whatsapp_number: string | null;
  auth_provider: string;
  email_enabled: boolean;
  email_address: string | null;
}

export { UserService };
export const userService = new UserService();

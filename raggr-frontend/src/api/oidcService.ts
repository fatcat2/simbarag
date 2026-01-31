/**
 * OIDC Authentication Service
 * Handles OAuth 2.0 Authorization Code flow with PKCE
 */

interface OIDCLoginResponse {
  auth_url: string;
}

interface OIDCCallbackResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    username: string;
    email: string;
  };
}

class OIDCService {
  private baseUrl = "/api/user/oidc";

  /**
   * Initiate OIDC login flow
   * Returns authorization URL to redirect user to
   */
  async initiateLogin(redirectAfterLogin: string = "/"): Promise<string> {
    const response = await fetch(
      `${this.baseUrl}/login?redirect=${encodeURIComponent(redirectAfterLogin)}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to initiate OIDC login");
    }

    const data: OIDCLoginResponse = await response.json();
    return data.auth_url;
  }

  /**
   * Handle OIDC callback
   * Exchanges authorization code for tokens
   */
  async handleCallback(
    code: string,
    state: string
  ): Promise<OIDCCallbackResponse> {
    const response = await fetch(
      `${this.baseUrl}/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!response.ok) {
      throw new Error("OIDC callback failed");
    }

    return await response.json();
  }

  /**
   * Extract OIDC callback parameters from URL
   */
  getCallbackParamsFromURL(): { code: string; state: string } | null {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");

    if (code && state) {
      return { code, state };
    }

    return null;
  }

  /**
   * Clear callback parameters from URL without reload
   */
  clearCallbackParams(): void {
    const url = new URL(window.location.href);
    url.searchParams.delete("code");
    url.searchParams.delete("state");
    url.searchParams.delete("error");
    window.history.replaceState({}, "", url.toString());
  }
}

export const oidcService = new OIDCService();

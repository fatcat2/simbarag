# Token Refresh Implementation

## Overview

The API services now automatically handle token refresh when access tokens expire. This provides a seamless user experience without requiring manual re-authentication.

## How It Works

### 1. **userService.ts**

The `userService` now includes:

- **`refreshToken()`**: Automatically gets the refresh token from localStorage, calls the `/api/user/refresh` endpoint, and updates the access token
- **`fetchWithAuth()`**: A wrapper around `fetch()` that:
  1. Automatically adds the Authorization header with the access token
  2. Detects 401 (Unauthorized) responses
  3. Automatically refreshes the token using the refresh token
  4. Retries the original request with the new access token
  5. Throws an error if refresh fails (e.g., refresh token expired)

### 2. **conversationService.ts**

Now uses `userService.fetchWithAuth()` for all API calls:
- `sendQuery()` - No longer needs token parameter
- `getMessages()` - No longer needs token parameter

### 3. **Components Updated**

**ChatScreen.tsx**:
- Removed manual token handling
- Now simply calls `conversationService.sendQuery(query)` and `conversationService.getMessages()`

## Benefits

✅ **Automatic token refresh** - Users stay logged in longer
✅ **Transparent retry logic** - Failed requests due to expired tokens are automatically retried
✅ **Cleaner code** - Components don't need to manage tokens
✅ **Better UX** - No interruptions when access token expires
✅ **Centralized auth logic** - All auth handling in one place

## Error Handling

- If refresh token is missing or invalid, the error is thrown
- Components can catch these errors and redirect to login
- LocalStorage is automatically cleared when refresh fails

## Usage Example

```typescript
// Old way (manual token management)
const token = localStorage.getItem("access_token");
const result = await conversationService.sendQuery(query, token);

// New way (automatic token refresh)
const result = await conversationService.sendQuery(query);
```

## Token Storage

- **Access Token**: `localStorage.getItem("access_token")`
- **Refresh Token**: `localStorage.getItem("refresh_token")`

Both are automatically managed by the services.

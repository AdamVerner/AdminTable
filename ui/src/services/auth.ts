import { notifications } from '@mantine/notifications';
import dataService, { AuthInfo } from '@/services/data.service';

const LS_KEY_AUTH = 'auth';
const LS_KEY_TOKEN = 'token';

class AuthService {
  async login(username: string, password: string, otp?: string): Promise<boolean> {
    localStorage.removeItem(LS_KEY_AUTH);
    const auth = await dataService.auth_login(username, password, otp);

    // Store the token in the local storage
    localStorage.setItem(LS_KEY_AUTH, JSON.stringify(auth));
    localStorage.setItem(LS_KEY_TOKEN, auth.access_token);

    // refresh token after timeout
    setTimeout(async () => {
      await this.refresh();
    }, auth.token_lifetime * 1000);

    return true;
  }

  async refresh() {
    const auth_raw = localStorage.getItem(LS_KEY_AUTH);
    if (auth_raw == null) {
      return false;
    }

    const auth = JSON.parse(auth_raw) as AuthInfo;
    let new_auth;
    try {
      new_auth = await dataService.auth_refresh(auth.refresh_token);
    } catch (e) {
      notifications.show({
        title: 'Session expired',
        message: 'Please log in again.',
        color: 'red',
        autoClose: 15000,
      });
      localStorage.removeItem(LS_KEY_AUTH);
      localStorage.removeItem(LS_KEY_TOKEN);
      document.location.reload();
      return false;
    }

    localStorage.setItem(LS_KEY_AUTH, JSON.stringify(new_auth));
    localStorage.setItem(LS_KEY_TOKEN, new_auth.access_token);

    setTimeout(async () => {
      await this.refresh();
    }, new_auth.token_lifetime * 1000);
  }

  async isUserLoggedIn(): Promise<boolean> {
    const auth = localStorage.getItem(LS_KEY_AUTH);
    if (auth == null) {
      return false;
    }
    try {
      await dataService.ping();
      return true;
    } catch (e) {
      return false;
    }
  }

  async logout() {
    // call dataService.auth_logout with refresh token to invalidate it and then remove everything from localstorage.

    const auth = localStorage.getItem(LS_KEY_AUTH);
    if (auth == null) {
      return;
    }
    const auth_raw = JSON.parse(auth) as AuthInfo;
    try {
      await dataService.auth_logout(auth_raw.refresh_token);
    } finally {
      localStorage.removeItem(LS_KEY_AUTH);
      localStorage.removeItem(LS_KEY_TOKEN);
    }
  }

  getHeaders(): { Authorization?: string } {
    const token = localStorage.getItem(LS_KEY_TOKEN);
    if (token == null) {
      return {};
    }
    return { Authorization: `Bearer ${token}` };
  }
}

export const authService = new AuthService();

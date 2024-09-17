import dataService from "@/services/data.service";
import {redirect} from "react-router-dom";

class UnauthenticatedError extends Error {}
class AuthService {
  async login(username: string, password: string): Promise<boolean> {
    localStorage.removeItem('user');
    const auth = await dataService.login(username, password);
    const user = { token: auth.token };
    // Store the token in the local storage
    localStorage.setItem('user', JSON.stringify(user));
    return true;
  }

  async isUserLoggedIn(): Promise<boolean> {
    const user = localStorage.getItem('user');
    if (user == null) {
        return false;
    }
    try {
        await dataService.ping();
        return true;
    }
    catch (e) {
        return false;
    }
  }

    logout() {
    // Remove the token from the local storage
    localStorage.removeItem('user');
  }


  getHeaders(): { Authorization?: string } {
    const user = localStorage.getItem('user');
    if (user == null) {
      return {}
    }
    return { Authorization: `Bearer ${JSON.parse(user)?.token}` };
  }
}

export const authService = new AuthService();

class UnauthenticatedError extends Error {}
class AuthService {
  async login(username: string, password: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    if (username === 'admin@admin.admin' && password === 'admin@admin.admin') {
      // Store the token in the local storage
      localStorage.setItem('user', JSON.stringify({ token: 'admin' }));
      return true;
    }
    throw new UnauthenticatedError('Invalid username or password');
  }

  logout() {
    // Remove the token from the local storage
    localStorage.removeItem('user');
  }

  isUserLoggedIn(): boolean {
    const user = localStorage.getItem('user');
    return user != null;
    // todo check token expiration as well
  }

  getHeaders(): { Authorization: string } {
    const user = localStorage.getItem('user');
    if (user == null) {
      throw new UnauthenticatedError('User is not logged in');
    }
    return { Authorization: `Bearer ${JSON.parse(user).token}` };
  }
}

export const authService = new AuthService();

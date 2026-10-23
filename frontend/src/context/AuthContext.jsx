import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Restore active user session on app load
  const loadUser = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getCurrentUser();
      if (data?.user) {
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email, password) => {
    setAuthError(null);
    try {
      const data = await api.login(email, password);
      if (data?.user) {
        setUser(data.user);
        return data.user;
      }
      throw new Error(data?.message || 'Login failed');
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  const register = async (email, password, fullName, organization) => {
    setAuthError(null);
    try {
      const data = await api.register(email, password, fullName, organization);
      if (data?.user) {
        setUser(data.user);
        return data.user;
      }
      throw new Error(data?.message || 'Registration failed');
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setAuthError(null);
    }
  };

  const refreshProfile = async () => {
    try {
      const data = await api.getCurrentUser();
      if (data?.user) {
        setUser(data.user);
      }
    } catch {
      // Keep existing user if transient network failure
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: Boolean(user),
        authError,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

const DEFAULT_LOCAL_USER = {
  id: 'local_user',
  name: 'Local Auditor',
  email: 'auditor@local.device',
  organization: 'Local Workspace',
  role: 'auditor',
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(DEFAULT_LOCAL_USER);
  const [isLoading] = useState(false);
  const [authError] = useState(null);

  const login = async () => {
    return DEFAULT_LOCAL_USER;
  };

  const register = async () => {
    return DEFAULT_LOCAL_USER;
  };

  const logout = async () => {
    // Single user local session reset
    setUser(DEFAULT_LOCAL_USER);
  };

  const refreshProfile = async () => {
    setUser(DEFAULT_LOCAL_USER);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: true,
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

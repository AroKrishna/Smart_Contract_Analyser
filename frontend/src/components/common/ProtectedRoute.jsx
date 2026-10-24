import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, ArrowLeft, Loader2 } from 'lucide-react';
import Button from './Button';
import Card from './Card';

const ProtectedRoute = ({ children }) => {
  return children;
};

export default ProtectedRoute;

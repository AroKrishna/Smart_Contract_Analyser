import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, ArrowLeft, Loader2 } from 'lucide-react';
import Button from './Button';
import Card from './Card';

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-xs text-slate-400 font-mono">Verifying authentication session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="max-w-md mx-auto my-12">
        <Card className="border-red-500/30 bg-red-950/20 text-center p-8 space-y-4 shadow-xl">
          <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-100">Access Restricted</h3>
            <p className="text-xs text-slate-400">
              The requested administrative workspace requires <span className="font-semibold text-slate-200">{requiredRole}</span> role privileges.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/dashboard">
              <Button variant="outline" size="sm" icon={ArrowLeft}>
                Return to Dashboard
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;

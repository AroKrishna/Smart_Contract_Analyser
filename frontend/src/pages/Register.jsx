import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, User, Mail, Lock, Building, ArrowRight, AlertCircle } from 'lucide-react';
import { APP_NAME } from '../utils/constants';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Card from '../components/common/Card';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [organization, setOrganization] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match');
      return;
    }

    if (!agreedToTerms) {
      setErrorMessage('Please accept the decision-support terms to continue');
      return;
    }

    setIsLoading(true);

    try {
      await register(email.trim(), password, name.trim(), organization.trim());
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setErrorMessage(err.message || 'Registration could not be completed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4 group">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/30 text-blue-400 group-hover:border-blue-400 transition-colors">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="font-semibold text-lg text-slate-100">{APP_NAME}</span>
          </Link>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">
            Create an auditor account
          </h2>
          <p className="text-xs text-slate-400 mt-1.5">
            Start auditing Solidity smart contracts for legal and compliance risks
          </p>
        </div>

        {/* Register Card */}
        <Card className="border-slate-800 bg-slate-900/90 shadow-xl">
          {errorMessage && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name"
              id="name"
              type="text"
              placeholder="Jane Doe"
              icon={User}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />

            <Input
              label="Work Email"
              id="email"
              type="email"
              placeholder="jane@company.com"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Organization / Project (Optional)"
              id="organization"
              type="text"
              placeholder="Protocol Labs / Security DAO"
              icon={Building}
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
            />

            <Input
              label="Password"
              id="password"
              type="password"
              placeholder="••••••••"
              icon={Lock}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Input
              label="Confirm Password"
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              icon={Lock}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            {/* Terms / Disclaimer Consent */}
            <div className="pt-2">
              <label className="flex items-start gap-2.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500/40"
                  required
                />
                <span className="text-xs text-slate-400 leading-relaxed">
                  I understand that {APP_NAME} provides automated decision-support risk analysis and does not constitute definitive legal advice or guarantees.
                </span>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-3"
              isLoading={isLoading}
              icon={ArrowRight}
              iconPosition="right"
            >
              Register & Launch Dashboard
            </Button>
          </form>

          {/* Existing Account Link */}
          <div className="mt-6 pt-5 border-t border-slate-800 text-center">
            <p className="text-xs text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Register;

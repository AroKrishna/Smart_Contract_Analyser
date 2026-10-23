import { useState, useEffect } from 'react';
import { User, Mail, Building, ShieldCheck, Check, Key, Lock, AlertCircle } from 'lucide-react';
import Card from '../components/common/Card';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

const Profile = () => {
  const { user, refreshUser } = useAuth();

  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [organization, setOrganization] = useState(user?.organization || '');
  const [role, setRole] = useState(user?.role || 'auditor');
  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [profileError, setProfileError] = useState('');

  // Password Modal State
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setEmail(user.email || '');
      setOrganization(user.organization || '');
      setRole(user.role || 'auditor');
    }
  }, [user]);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long');
      return;
    }

    setIsPasswordLoading(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      setPasswordSuccess(true);
      setTimeout(() => {
        setPasswordSuccess(false);
        setPasswordModalOpen(false);
        setCurrentPassword('');
        setNewPassword('');
      }, 1500);
    } catch (err) {
      setPasswordError(err.message || 'Failed to update password');
    } finally {
      setIsPasswordLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setProfileError('');
    setIsSaving(true);
    try {
      await api.updateProfile({ name, organization });
      if (refreshUser) await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setProfileError(err.message || 'Failed to save profile changes');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-2xl font-bold tracking-tight text-slate-100">
          Auditor Profile
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Manage your personal auditing credentials and organization affiliation
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Auditor Card */}
        <Card className="border-slate-800 bg-slate-900/60 p-6 flex flex-col items-center text-center">
          <div className="w-20 h-20 rounded-full bg-blue-600/20 border-2 border-blue-500/40 flex items-center justify-center text-2xl font-bold text-blue-300 mb-4 shadow-lg shadow-blue-500/10">
            JD
          </div>
          <h3 className="text-base font-bold text-slate-100">{name}</h3>
          <p className="text-xs text-blue-400 mt-0.5">{role}</p>
          <p className="text-xs text-slate-400 mt-1 font-medium">{organization}</p>

          <div className="w-full mt-6 pt-6 border-t border-slate-800/80 space-y-2.5 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Audits Completed</span>
              <span className="font-mono text-slate-200 font-semibold">48</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>High Risks Identified</span>
              <span className="font-mono text-amber-400 font-semibold">11</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Model Access</span>
              <span className="text-slate-300">Legal-BERT Enterprise</span>
            </div>
          </div>
        </Card>

        {/* Right Column: Profile Edit Form */}
        <div className="md:col-span-2">
          <Card
            title="Profile Credentials"
            subtitle="Update your auditor information and primary contact email"
            className="border-slate-800 bg-slate-900/60 p-6"
          >
            {saved && (
              <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-center gap-2">
                <Check className="w-4 h-4 shrink-0" />
                <span>Profile information saved successfully.</span>
              </div>
            )}

            {profileError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{profileError}</span>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <Input
                label="Full Name"
                id="name"
                icon={User}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />

              <Input
                label="Email Address"
                id="email"
                type="email"
                icon={Mail}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Organization / Company"
                id="organization"
                icon={Building}
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
              />

              <Input
                label="Auditor Role"
                id="role"
                icon={ShieldCheck}
                value={role}
                onChange={(e) => setRole(e.target.value)}
              />

              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setPasswordModalOpen(true)}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5"
                >
                  <Key className="w-3.5 h-3.5" />
                  Change Password
                </button>

                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isSaving}
                >
                  Save Changes
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>

      {/* Change Password Modal */}
      <Modal
        isOpen={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
        title="Update Account Password"
        subtitle="Ensure your auditor account uses a secure passphrase"
      >
        {passwordSuccess ? (
          <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-center gap-2">
            <Check className="w-4 h-4 shrink-0" />
            <span>Password updated successfully.</span>
          </div>
        ) : (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {passwordError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{passwordError}</span>
              </div>
            )}

            <Input
              label="Current Password"
              id="currentPassword"
              type="password"
              icon={Lock}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />

            <Input
              label="New Password (min 8 characters)"
              id="newPassword"
              type="password"
              icon={Lock}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />

            <div className="flex justify-end gap-2.5 pt-2">
              <Button
                variant="secondary"
                size="sm"
                type="button"
                onClick={() => setPasswordModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                type="submit"
                isLoading={isPasswordLoading}
              >
                Save New Password
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default Profile;

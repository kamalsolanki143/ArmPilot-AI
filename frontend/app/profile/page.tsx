"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import AppLayout from "@/components/AppLayout";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout, updateProfile } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Password change form state
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setEditName(user.fullName);
      setEditEmail(user.email);
    }
  }, [user]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0B0F19] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleSaveProfile = () => {
    updateProfile({ fullName: editName, email: editEmail });
    setIsEditing(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handlePasswordChange = () => {
    setPwError("");
    if (!currentPw) {
      setPwError("Current password is required.");
      return;
    }
    if (newPw.length < 8) {
      setPwError("New password must be at least 8 characters.");
      return;
    }
    if (newPw !== confirmPw) {
      setPwError("Passwords do not match.");
      return;
    }
    // Mock password change success
    setPwSuccess(true);
    setShowPasswordForm(false);
    setCurrentPw("");
    setNewPw("");
    setConfirmPw("");
    setTimeout(() => setPwSuccess(false), 3000);
  };

  const handleSignOut = () => {
    logout();
    router.push("/login");
  };

  const joinDate = new Date(user.joinedAt).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <AppLayout pageTitle="Profile">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Success toast */}
        {saveSuccess && (
          <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-400 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Profile updated successfully.
          </div>
        )}

        {pwSuccess && (
          <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-400 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Password changed successfully.
          </div>
        )}

        {/* ── Profile Header Card ── */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-full bg-[#E5D5C5] text-[#2C241D] flex items-center justify-center font-bold text-2xl shadow-inner shrink-0">
              {user.avatarInitial}
            </div>

            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold text-white truncate">{user.fullName}</h2>
              <p className="text-sm text-zinc-400 truncate">{user.email}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 border border-orange-500/20 text-xs font-medium">
                  {user.role}
                </span>
                <span className="text-xs text-zinc-500 font-mono">Joined {joinDate}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3.5 py-2 rounded-lg bg-[#162032] hover:bg-[#1F293D] text-zinc-200 text-xs font-medium border border-[#1F293D] transition-colors"
                >
                  Edit Profile
                </button>
              )}
              <button
                onClick={handleSignOut}
                className="px-3.5 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-medium border border-red-500/20 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>

        {/* ── Account Information ── */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#1F293D]">
            <h3 className="text-sm font-semibold text-white">Account Information</h3>
          </div>

          <div className="p-6 space-y-4">
            {isEditing ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-400">Full Name</label>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-white text-sm focus:outline-none focus:border-orange-500/60 focus:ring-1 focus:ring-orange-500/30 transition-colors"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-400">Email Address</label>
                    <input
                      type="email"
                      value={editEmail}
                      onChange={(e) => setEditEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-white text-sm focus:outline-none focus:border-orange-500/60 focus:ring-1 focus:ring-orange-500/30 transition-colors"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={handleSaveProfile}
                    className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs font-semibold transition-colors"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditName(user.fullName);
                      setEditEmail(user.email);
                    }}
                    className="px-4 py-2 rounded-lg bg-[#162032] hover:bg-[#1F293D] text-zinc-300 text-xs font-medium border border-[#1F293D] transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8">
                <div>
                  <span className="block text-xs text-zinc-500 font-medium mb-0.5">Full Name</span>
                  <span className="text-sm text-white">{user.fullName}</span>
                </div>
                <div>
                  <span className="block text-xs text-zinc-500 font-medium mb-0.5">Email</span>
                  <span className="text-sm text-white">{user.email}</span>
                </div>
                <div>
                  <span className="block text-xs text-zinc-500 font-medium mb-0.5">Role</span>
                  <span className="text-sm text-white">{user.role}</span>
                </div>
                <div>
                  <span className="block text-xs text-zinc-500 font-medium mb-0.5">User ID</span>
                  <span className="text-sm text-zinc-300 font-mono">{user.id}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Security Section ── */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#1F293D] flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Security</h3>
            {!showPasswordForm && (
              <button
                onClick={() => setShowPasswordForm(true)}
                className="text-xs text-orange-400 hover:text-orange-300 font-medium transition-colors"
              >
                Change Password
              </button>
            )}
          </div>

          <div className="p-6">
            {showPasswordForm ? (
              <div className="space-y-4 max-w-md">
                {pwError && (
                  <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
                    {pwError}
                  </div>
                )}
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-zinc-400">Current Password</label>
                  <input
                    type="password"
                    value={currentPw}
                    onChange={(e) => setCurrentPw(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-white text-sm focus:outline-none focus:border-orange-500/60 focus:ring-1 focus:ring-orange-500/30 transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-zinc-400">New Password</label>
                  <input
                    type="password"
                    value={newPw}
                    onChange={(e) => setNewPw(e.target.value)}
                    placeholder="Min. 8 characters"
                    className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-orange-500/60 focus:ring-1 focus:ring-orange-500/30 transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-zinc-400">Confirm New Password</label>
                  <input
                    type="password"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-white text-sm focus:outline-none focus:border-orange-500/60 focus:ring-1 focus:ring-orange-500/30 transition-colors"
                  />
                </div>
                <div className="flex items-center gap-3 pt-1">
                  <button
                    onClick={handlePasswordChange}
                    className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs font-semibold transition-colors"
                  >
                    Update Password
                  </button>
                  <button
                    onClick={() => {
                      setShowPasswordForm(false);
                      setPwError("");
                      setCurrentPw("");
                      setNewPw("");
                      setConfirmPw("");
                    }}
                    className="px-4 py-2 rounded-lg bg-[#162032] hover:bg-[#1F293D] text-zinc-300 text-xs font-medium border border-[#1F293D] transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <div>
                    <span className="text-sm text-white block">Password</span>
                    <span className="text-xs text-zinc-500">Last changed: Never</span>
                  </div>
                  <span className="text-xs font-mono text-zinc-400">••••••••••</span>
                </div>
                <div className="border-t border-[#1F293D]/60 pt-3 flex items-center justify-between">
                  <div>
                    <span className="text-sm text-white block">Two-factor authentication</span>
                    <span className="text-xs text-zinc-500">Add an extra layer of security</span>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-700/40 text-zinc-400 border border-[#1F293D]">
                    Not enabled
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Connected Accounts ── */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#1F293D]">
            <h3 className="text-sm font-semibold text-white">Connected Accounts</h3>
          </div>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#0B0F19] border border-[#1F293D] flex items-center justify-center">
                  <svg className="w-4 h-4 text-zinc-300" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                </div>
                <div>
                  <span className="text-sm text-white block">GitHub</span>
                  <span className="text-xs text-zinc-500">Not connected</span>
                </div>
              </div>
              <button className="px-3 py-1.5 rounded-lg bg-[#162032] hover:bg-[#1F293D] text-zinc-300 text-xs font-medium border border-[#1F293D] transition-colors">
                Connect
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

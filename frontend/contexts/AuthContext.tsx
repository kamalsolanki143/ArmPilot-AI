"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

export interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  role: string;
  avatarInitial: string;
  joinedAt: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (fullName: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateProfile: (updates: Partial<Pick<AuthUser, "fullName" | "email">>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "armpilot_auth_user";

// Demo user seeded on first login
const DEMO_USER: AuthUser = {
  id: "usr_arm64_001",
  fullName: "Kamal Solanki",
  email: "kamal@armpilot.dev",
  role: "Platform Engineer",
  avatarInitial: "K",
  joinedAt: "2025-06-01T00:00:00Z",
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(false);

  const persistUser = useCallback((u: AuthUser) => {
    setUser(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
      // Simulate network delay for realism
      await new Promise((r) => setTimeout(r, 800));

      if (!email.trim() || !password.trim()) {
        return { success: false, error: "Email and password are required." };
      }
      if (password.length < 6) {
        return { success: false, error: "Invalid credentials." };
      }

      // Create user from email or use demo defaults
      const namePart = email.split("@")[0].replace(/[._-]/g, " ");
      const formattedName = namePart
        .split(" ")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ");

      const authUser: AuthUser = {
        ...DEMO_USER,
        email,
        fullName: formattedName || DEMO_USER.fullName,
        avatarInitial: (formattedName || DEMO_USER.fullName).charAt(0).toUpperCase(),
      };

      persistUser(authUser);
      return { success: true };
    },
    [persistUser],
  );

  const signup = useCallback(
    async (fullName: string, email: string, password: string): Promise<{ success: boolean; error?: string }> => {
      await new Promise((r) => setTimeout(r, 1000));

      if (!fullName.trim()) return { success: false, error: "Full name is required." };
      if (!email.trim()) return { success: false, error: "Email is required." };
      if (!email.includes("@")) return { success: false, error: "Please enter a valid email address." };
      if (password.length < 8) return { success: false, error: "Password must be at least 8 characters." };

      const authUser: AuthUser = {
        id: `usr_${Date.now()}`,
        fullName: fullName.trim(),
        email: email.trim().toLowerCase(),
        role: "Platform Engineer",
        avatarInitial: fullName.trim().charAt(0).toUpperCase(),
        joinedAt: new Date().toISOString(),
      };

      persistUser(authUser);
      return { success: true };
    },
    [persistUser],
  );

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const updateProfile = useCallback(
    (updates: Partial<Pick<AuthUser, "fullName" | "email">>) => {
      if (!user) return;
      const updated = {
        ...user,
        ...updates,
        avatarInitial: (updates.fullName || user.fullName).charAt(0).toUpperCase(),
      };
      persistUser(updated);
    },
    [user, persistUser],
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

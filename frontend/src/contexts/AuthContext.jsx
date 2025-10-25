import React, { createContext, useContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Admin state
  const [adminUser, setAdminUser] = useState(null);
  const [adminToken, setAdminToken] = useState(null);

  // Session type tracking
  const [sessionType, setSessionType] = useState(null); // 'user' | 'admin' | null

  // Tab isolation - generate unique tab ID
  const [tabId] = useState(
    () => `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );

  // Simple tab isolation using sessionStorage priority
  useEffect(() => {
    // Tab initialization without logging to prevent render issues
  }, [tabId]);

  // Check for existing token on mount
  useEffect(() => {
    // Use sessionStorage for tab-specific data to prevent cross-tab interference
    const savedToken =
      sessionStorage.getItem("access_token") ||
      localStorage.getItem("access_token");
    const savedUser =
      sessionStorage.getItem("user") || localStorage.getItem("user");
    const savedAdminToken =
      sessionStorage.getItem("admin_token") ||
      localStorage.getItem("admin_token");
    const savedAdminUser =
      sessionStorage.getItem("admin_user") ||
      localStorage.getItem("admin_user");

    // Allow dual sessions - both user and admin can be logged in simultaneously
    console.log("AuthContext: Loading existing sessions", {
      hasUserSession: !!savedToken,
      hasAdminSession: !!savedAdminToken,
    });

    if (savedToken && savedUser) {
      try {
        // Check if token is still valid
        const decoded = jwtDecode(savedToken);
        const currentTime = Date.now() / 1000;

        if (decoded.exp > currentTime) {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        } else {
          // Token expired, clear storage
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
        }
      } catch (error) {
        console.error("Error decoding token:", error);
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
      }
    }

    if (savedAdminToken && savedAdminUser) {
      try {
        // Check if admin token is still valid
        const decoded = jwtDecode(savedAdminToken);
        const currentTime = Date.now() / 1000;

        if (decoded.exp > currentTime) {
          setAdminToken(savedAdminToken);
          setAdminUser(JSON.parse(savedAdminUser));
        } else {
          // Admin token expired, clear storage
          localStorage.removeItem("admin_token");
          localStorage.removeItem("admin_user");
        }
      } catch (error) {
        console.error("Error decoding admin token:", error);
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_user");
      }
    }

    setLoading(false);
  }, []);

  const login = async (googleToken) => {
    try {
      console.log("AuthContext: Starting user login process...");

      // Clear only user session data, keep admin session intact
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      setToken(null);
      setUser(null);

      const API_BASE_URL =
        process.env.REACT_APP_BACKEND_URL ||
        (window.__ENV__ && window.__ENV__.REACT_APP_BACKEND_URL) ||
        "http://localhost:8001";
      console.log("AuthContext: Using API URL:", API_BASE_URL);
      const response = await fetch(`${API_BASE_URL}/auth/google`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: googleToken }),
      });

      console.log("AuthContext: Response status:", response.status);
      console.log("AuthContext: Response headers:", response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("AuthContext: Response error:", errorText);
        console.error("AuthContext: Full response:", response);
        console.error("AuthContext: Response status:", response.status);
        console.error("AuthContext: Response statusText:", response.statusText);

        // Try to parse error as JSON if possible
        let errorJson = null;
        try {
          errorJson = JSON.parse(errorText);
          console.error("AuthContext: Parsed error JSON:", errorJson);
        } catch (e) {
          console.error("AuthContext: Error text is not JSON:", errorText);
        }

        // Handle specific token timing errors
        if (
          errorJson &&
          errorJson.detail &&
          errorJson.detail.includes("Token used too early")
        ) {
          console.log(
            "AuthContext: Token timing issue detected, retrying in 2 seconds..."
          );
          await new Promise((resolve) => setTimeout(resolve, 2000));

          // Retry the request
          const retryResponse = await fetch(`${API_BASE_URL}/auth/google`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ token: googleToken }),
          });

          if (retryResponse.ok) {
            const retryData = await retryResponse.json();
            console.log("AuthContext: Retry authentication successful");

            // Save to both sessionStorage (priority) and localStorage (backup)
            sessionStorage.setItem("access_token", retryData.access_token);
            sessionStorage.setItem("user", JSON.stringify(retryData.user));
            localStorage.setItem("access_token", retryData.access_token);
            localStorage.setItem("user", JSON.stringify(retryData.user));

            // Update state
            setToken(retryData.access_token);
            setUser(retryData.user);

            console.log(
              "AuthContext: Login completed successfully after retry"
            );
            return retryData;
          }
        }

        throw new Error(
          `Authentication failed: ${response.status} - ${errorText}`
        );
      }

      const data = await response.json();
      console.log("AuthContext: Response data:", data);

      // Save to both sessionStorage (priority) and localStorage (backup)
      sessionStorage.setItem("access_token", data.access_token);
      sessionStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      // Update state
      setToken(data.access_token);
      setUser(data.user);

      console.log("AuthContext: Login completed successfully");
      return data;
    } catch (error) {
      console.error("AuthContext: Login error:", error);
      // Clear any partial authentication data on error
      forceLogout();
      throw error;
    }
  };

  const logout = async () => {
    console.log("AuthContext: Starting logout process...");

    try {
      // Call backend logout endpoint if user is authenticated
      if (token) {
        const API_BASE_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (window.__ENV__ && window.__ENV__.REACT_APP_BACKEND_URL) ||
  "http://localhost:8001";
        console.log("AuthContext: Calling backend logout endpoint...");

        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          console.log("AuthContext: Backend logout successful:", data);
          console.log(
            `AuthContext: Deactivated ${data.sessions_deactivated} sessions`
          );
        } else {
          console.warn(
            "AuthContext: Backend logout failed, but continuing with frontend logout"
          );
        }
      }
    } catch (error) {
      console.error("AuthContext: Error calling backend logout:", error);
      console.log(
        "AuthContext: Continuing with frontend logout despite backend error"
      );
    }

    // Clear both sessionStorage and localStorage
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    // Clear state
    setToken(null);
    setUser(null);

    // Sign out from Google more thoroughly
    if (window.google && window.google.accounts) {
      console.log("AuthContext: Signing out from Google...");
      try {
        // Disable auto-select
        window.google.accounts.id.disableAutoSelect();

        // Revoke the current session
        window.google.accounts.id.revoke(token, (done) => {
          console.log("AuthContext: Google token revoked:", done);
        });

        // Clear any Google session cookies
        document.cookie =
          "g_state=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.google.com;";
        document.cookie =
          "g_csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.google.com;";
      } catch (error) {
        console.warn("AuthContext: Error during Google sign-out:", error);
      }
    }

    console.log("AuthContext: Logout completed");
  };

  const forceLogout = () => {
    console.log("AuthContext: Force logout - clearing all authentication data");

    // Clear localStorage immediately
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    // Clear state
    setToken(null);
    setUser(null);

    // Clear Google session
    if (window.google && window.google.accounts) {
      try {
        window.google.accounts.id.disableAutoSelect();
      } catch (error) {
        console.warn("AuthContext: Error during force Google sign-out:", error);
      }
    }

    console.log("AuthContext: Force logout completed");
  };

  const isTokenExpired = (token) => {
    if (!token) return true;

    try {
      // Decode JWT token to check expiry
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Math.floor(Date.now() / 1000);

      // Check if token is expired (with 30 second buffer)
      return payload.exp < currentTime + 30;
    } catch (error) {
      console.error("AuthContext: Error checking token expiry:", error);
      return true; // Assume expired if can't decode
    }
  };

  const getAuthHeaders = () => {
    if (token && !isTokenExpired(token)) {
      return {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };
    } else if (token && isTokenExpired(token)) {
      // Token is expired, clear it
      console.log("AuthContext: Token expired, clearing authentication");
      logout();
      return {
        "Content-Type": "application/json",
      };
    }
    return {
      "Content-Type": "application/json",
    };
  };

  // Admin functions
  const loginAdmin = async (email, password) => {
    try {
      console.log("AuthContext: Starting admin login process...");

      // Clear only admin session data, keep user session intact
      localStorage.removeItem("admin_token");
      localStorage.removeItem("admin_user");
      setAdminToken(null);
      setAdminUser(null);

      const API_BASE_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (window.__ENV__ && window.__ENV__.REACT_APP_BACKEND_URL) ||
  "http://localhost:8001";
      const response = await fetch(`${API_BASE_URL}/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Admin login failed");
      }

      const data = await response.json();
      console.log("AuthContext: Admin login successful");

      // Save to both sessionStorage (priority) and localStorage (backup)
      sessionStorage.setItem("admin_token", data.access_token);
      sessionStorage.setItem(
        "admin_user",
        JSON.stringify({ email: data.admin_email })
      );
      localStorage.setItem("admin_token", data.access_token);
      localStorage.setItem(
        "admin_user",
        JSON.stringify({ email: data.admin_email })
      );

      // Update state
      setAdminToken(data.access_token);
      setAdminUser({ email: data.admin_email });

      return data;
    } catch (error) {
      console.error("AuthContext: Admin login error:", error);
      throw error;
    }
  };

  const logoutAdmin = () => {
    console.log("AuthContext: Admin logout");

    // Clear both sessionStorage and localStorage
    sessionStorage.removeItem("admin_token");
    sessionStorage.removeItem("admin_user");
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");

    // Clear state
    setAdminToken(null);
    setAdminUser(null);
  };

  const getAdminAuthHeaders = () => {
    if (adminToken && !isTokenExpired(adminToken)) {
      return {
        Authorization: `Bearer ${adminToken}`,
        "Content-Type": "application/json",
      };
    } else if (adminToken && isTokenExpired(adminToken)) {
      // Admin token is expired, clear it
      console.log("AuthContext: Admin token expired, clearing authentication");
      logoutAdmin();
      return {
        "Content-Type": "application/json",
      };
    }
    return {
      "Content-Type": "application/json",
    };
  };

  const getAdminAuthHeadersForUpload = () => {
    if (adminToken && !isTokenExpired(adminToken)) {
      return {
        Authorization: `Bearer ${adminToken}`,
        // Don't set Content-Type for FormData uploads
      };
    } else if (adminToken && isTokenExpired(adminToken)) {
      // Admin token is expired, clear it
      console.log("AuthContext: Admin token expired, clearing authentication");
      logoutAdmin();
      return {};
    }
    return {};
  };

  // Session separation functions
  const clearAllSessions = () => {
    console.log("AuthContext: Clearing all sessions");
    sessionStorage.clear();
    localStorage.clear();
    setToken(null);
    setUser(null);
    setAdminToken(null);
    setAdminUser(null);
    setSessionType(null);
  };

  // Check if user has required session type for the route
  const hasRequiredSession = (requiredType) => {
    if (requiredType === "user") {
      return !!user && !!token;
    } else if (requiredType === "admin") {
      return !!adminUser && !!adminToken;
    }
    return false;
  };

  // Check if user is trying to access wrong interface
  const isWrongInterface = (currentPath, userType) => {
    const isAdminPath = currentPath.startsWith("/admin");
    const isUserPath = !isAdminPath;

    if (userType === "user" && isAdminPath) {
      return true; // User trying to access admin interface
    }
    if (userType === "admin" && isUserPath) {
      return true; // Admin trying to access user interface
    }
    return false;
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    forceLogout,
    getAuthHeaders,
    isAuthenticated: !!user,
    // Admin functions
    adminUser,
    adminToken,
    loginAdmin,
    logoutAdmin,
    getAdminAuthHeaders,
    getAdminAuthHeadersForUpload,
    isAdminAuthenticated: !!adminUser,
    // Session separation
    sessionType,
    clearAllSessions,
    hasRequiredSession,
    isWrongInterface,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

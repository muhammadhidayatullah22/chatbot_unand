import React, { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

// Session Guard Component to prevent cross-interface access
const SessionGuard = ({ children, requiredSessionType }) => {
  const { user, adminUser, hasRequiredSession, isWrongInterface, loading } =
    useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Skip check during loading
    if (loading) return;

    const currentPath = location.pathname;

    console.log("SessionGuard: Checking interface access", {
      currentPath,
      requiredSessionType,
      hasUser: !!user,
      hasAdmin: !!adminUser,
      hasRequiredSession: hasRequiredSession(requiredSessionType),
    });

    // Check if user has the required session for this route
    if (!hasRequiredSession(requiredSessionType)) {
      console.log(
        `SessionGuard: No ${requiredSessionType} session found, redirecting to login`
      );

      // Redirect to appropriate login
      if (requiredSessionType === "admin") {
        navigate("/login", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
      return;
    }

    // Prevent users from accessing wrong interface
    // If user is logged in and trying to access admin interface (except login page)
    if (
      user &&
      isWrongInterface(currentPath, "user") &&
      currentPath !== "/admin/login"
    ) {
      console.log(
        "SessionGuard: User trying to access admin interface, redirecting to user interface"
      );
      navigate("/", { replace: true });
      return;
    }

    // If admin is logged in and trying to access user interface
    if (adminUser && isWrongInterface(currentPath, "admin")) {
      console.log(
        "SessionGuard: Admin trying to access user interface, redirecting to admin dashboard"
      );
      navigate("/admin/dashboard", { replace: true });
      return;
    }
  }, [
    user,
    adminUser,
    requiredSessionType,
    location.pathname,
    navigate,
    hasRequiredSession,
    isWrongInterface,
    loading,
  ]);

  // Show loading during session check
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-green-50 to-yellow-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Memeriksa sesi...</p>
        </div>
      </div>
    );
  }

  return children;
};

export default SessionGuard;

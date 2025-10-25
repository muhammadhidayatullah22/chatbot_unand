import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";

const Login = () => {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const googleButtonRef = useRef(null);

  const handleCredentialResponse = async (response) => {
    console.log("Google credential response:", response);
    setLoading(true);
    setError(null);

    try {
      console.log("Attempting login with token...");
      await login(response.credential);
      console.log("Login successful!");
    } catch (error) {
      console.error("Login error details:", error);
      setError(`Login failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Initialize Google Sign-In function
  const initializeGoogleSignIn = () => {
    if (window.google && window.google.accounts) {
const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || 
                 (window.__ENV__ && window.__ENV__.REACT_APP_GOOGLE_CLIENT_ID) ||
                 null
      console.log("✅ Initializing Google Sign-In...");
      console.log("🔑 Client ID:", clientId);
      console.log("🌐 Current origin:", window.location.origin);
      console.log("📍 Button ref current:", !!googleButtonRef.current);

      // Clear any existing Google session first
      try {
        window.google.accounts.id.disableAutoSelect();
        console.log("🧹 Cleared existing Google auto-select");
      } catch (e) {
        console.log("ℹ️ No existing Google session to clear");
      }

      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
          use_fedcm_for_prompt: false, // Disable FedCM to avoid conflicts
          itp_support: true, // Enable Intelligent Tracking Prevention support
        });
        console.log("✅ Google Sign-In initialized successfully");

        // Render the Google Sign-In button
        if (googleButtonRef.current) {
          console.log("🎨 Rendering Google Sign-In button...");
          window.google.accounts.id.renderButton(googleButtonRef.current, {
            theme: "outline",
            size: "large",
            width: "100%",
            text: "signin_with",
            locale: "id",
          });
          console.log("✅ Google Sign-In button rendered");
        } else {
          console.error("❌ Button ref is null, cannot render button");
          setError("Tidak dapat menampilkan tombol login Google");
        }
      } catch (error) {
        console.error("❌ Error initializing Google Sign-In:", error);
        setError("Gagal menginisialisasi Google Sign-In: " + error.message);
      }
    } else {
      console.error("Google Identity Services not loaded");
      setError("Google Identity Services tidak dapat dimuat");
    }
  };

  // Function to load Google script manually if not loaded
  const loadGoogleScript = () => {
    return new Promise((resolve, reject) => {
      if (window.google && window.google.accounts) {
        resolve();
        return;
      }

      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => {
        console.log("✅ Google script loaded manually");
        // Wait a bit for the script to initialize
        setTimeout(() => {
          if (window.google && window.google.accounts) {
            resolve();
          } else {
            reject(new Error("Google script loaded but API not available"));
          }
        }, 500);
      };
      script.onerror = () => {
        reject(new Error("Failed to load Google script"));
      };
      document.head.appendChild(script);
    });
  };

  useEffect(() => {
    // Initialize Google Sign-In when component mounts
    console.log("🚀 Login component mounted, checking Google script...");
    console.log(
      "🔑 Google Client ID from env:",
      process.env.REACT_APP_GOOGLE_CLIENT_ID
    );
    console.log("🌐 Window.google available:", !!window.google);
    console.log(
      "🌐 Window.google.accounts available:",
      !!(window.google && window.google.accounts)
    );

    const initializeGoogle = async () => {
      try {
        // First check if already loaded
        if (window.google && window.google.accounts) {
          console.log("✅ Google script already loaded");
          initializeGoogleSignIn();
          return;
        }

        // Try to load manually
        console.log("📥 Loading Google script manually...");
        await loadGoogleScript();
        initializeGoogleSignIn();
      } catch (error) {
        console.error("❌ Failed to load Google script:", error);
        setError(
          "Google Identity Services gagal dimuat. Silakan refresh halaman."
        );
      }
    };

    initializeGoogle();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Remove dependency to avoid infinite loop

  return (
    <div className="min-h-screen bg-gradient-to-r from-green-50 to-yellow-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
          {/* Logo and Title */}
          <div className="text-center mb-8">
            <div className="mx-auto w-20 h-20 bg-gradient-to-r from-green-600 to-yellow-500 rounded-full flex items-center justify-center mb-4">
              <span className="text-white text-2xl font-bold">U</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Chatbot UNAND
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              UNTUK KEDJAJAAN BANGSA
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">
              Masuk untuk mengakses chatbot peraturan kampus
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
              <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Google Sign-In Button Container */}
          <div className="mb-4">
            <div ref={googleButtonRef} className="w-full"></div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600 mr-3"></div>
              <span className="text-gray-600 dark:text-gray-400">
                Memproses login...
              </span>
            </div>
          )}

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Dengan masuk, Anda menyetujui penggunaan data untuk keperluan
              chatbot
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

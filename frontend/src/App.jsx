import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import ChatWindow from "./ChatWindow";
import ChatSidebar from "./ChatSidebar";
import TelegramButton from "./TelegramButton";
import ThemeToggle from "./components/ThemeToggle";
import Login from "./components/Login";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import AdminUpload from "./components/AdminUpload";
import SessionGuard from "./components/SessionGuard";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { getSessionMessages } from "./api";
import {
  SidebarProvider,
  SidebarTrigger,
  SidebarInset,
} from "./components/ui/sidebar";
import "./index.css"; // Pastikan Tailwind CSS diimpor

// --- LOGIC BARU: DETEKSI DOMAIN ---
/**
 * Fungsi ini memeriksa apakah domain yang diakses adalah domain admin.
 * @returns {boolean} - True jika domain adalah domain admin.
 */
const getIsAdminDomain = () => {
  if (typeof window === "undefined") {
    return false; // Menghindari error saat server-side rendering (jika ada)
  }
  const hostname = window.location.hostname;

  // Ambil domain admin dari environment variable atau hardcode
  // Pastikan Anda menambahkan REACT_APP_ADMIN_DOMAIN di docker-compose.yml
  const adminDomain =
    process.env.REACT_APP_ADMIN_DOMAIN || "admin.difunand.cloud";

  // Juga periksa untuk pengembangan lokal jika perlu
  return hostname === adminDomain;
};

// --- Komponen yang ada dipindahkan dan disesuaikan ---

// Protected Admin Route Component
const ProtectedAdminRoute = ({ children }) => {
  const { isAdminAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-green-50 to-yellow-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Memuat...</p>
        </div>
      </div>
    );
  }

  return isAdminAuthenticated ? children : <Navigate to="/login" replace />;
};

// Main App Component (HANYA UNTUK USER BIASA)
const MainApp = () => {
  const { user, loading } = useAuth();
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Halo! Saya adalah Chatbot UNAND. Saya siap membantu Anda dengan pertanyaan seputar peraturan kampus dan pemerintah. Silakan ajukan pertanyaan Anda!",
      isBot: true,
      timestamp: new Date(),
      is_greeting: true,
    },
  ]);

  // Reset state when user changes (login/logout)
  useEffect(() => {
    // Reset to initial state when user changes
    setCurrentSessionId(null);
    setMessages([
      {
        id: 1,
        text: "Halo! Saya adalah Chatbot UNAND. Saya siap membantu Anda dengan pertanyaan seputar peraturan kampus dan pemerintah. Silakan ajukan pertanyaan Anda!",
        isBot: true,
        timestamp: new Date(),
        is_greeting: true,
      },
    ]);
  }, [user]);

  const handleSessionSelect = async (sessionId) => {
    try {
      setCurrentSessionId(sessionId);
      const sessionMessages = await getSessionMessages(sessionId);

      // Convert API messages to frontend format
      const convertedMessages = sessionMessages.map((msg) => ({
        id: msg.id,
        text: msg.content,
        isBot: msg.message_type === "bot",
        timestamp: new Date(msg.timestamp),
        sources: msg.sources,
        sources_count: msg.sources ? msg.sources.length : 0,
        summary: msg.summary,
        suggestions: msg.suggestions,
      }));

      setMessages(convertedMessages);
    } catch (error) {
      console.error("Error loading session messages:", error);
      alert("Gagal memuat riwayat percakapan");
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([
      {
        id: 1,
        text: "Halo! Saya adalah Chatbot UNAND. Saya siap membantu Anda dengan pertanyaan seputar peraturan kampus dan pemerintah. Silakan ajukan pertanyaan Anda!",
        isBot: true,
        timestamp: new Date(),
        is_greeting: true,
      },
    ]);
  };

  // Handle loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-400 dark:border-gray-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Memuat...</p>
        </div>
      </div>
    );
  }

  // Handle unauthenticated state for user app
  if (!user) {
    return <Login />;
  }

  return (
    <SessionGuard requiredSessionType="user">
      <ThemeProvider>
        <SidebarProvider>
          <div className="h-screen bg-white dark:bg-gray-950 flex overflow-hidden relative w-full">
            {/* Sidebar */}
            <ChatSidebar
              currentSessionId={currentSessionId}
              onSessionSelect={handleSessionSelect}
              onNewChat={handleNewChat}
            />

            {/* Main Content */}
            <SidebarInset className="flex flex-1 flex-col w-full h-full min-w-0 overflow-hidden bg-white dark:bg-gray-950">
              <div className="border-b border-gray-200 dark:border-gray-800 p-3 min-w-0 lg:p-4 flex-shrink-0 bg-white dark:bg-gray-950 w-full">
                {/* Mobile Header */}
                <div className="flex lg:hidden items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <SidebarTrigger className="p-2" />
                    <img
                      src="/lambang-unand.jpg"
                      alt="Logo UNAND"
                      className="w-7 h-7 object-contain rounded"
                    />
                    <h1 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                      TANYO UNAND
                    </h1>
                  </div>
                  <ThemeToggle />
                </div>

                {/* Desktop Header */}
                <div className="hidden lg:flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    <SidebarTrigger className="p-2" />
                    <img
                      src="/lambang-unand.jpg"
                      alt="Logo Universitas Andalas"
                      className="w-10 h-10 object-contain rounded-lg"
                    />
                    <div className="flex flex-col justify-center">
                      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 leading-tight">
                        TANYO UNAND
                      </h1>
                      <p className="text-gray-600 dark:text-gray-400 text-xs leading-tight">
                        Chatbot Universitas Andalas
                      </p>
                    </div>
                  </div>
                  <ThemeToggle />
                </div>
              </div>

              {/* Chat Window */}
              <div className="flex flex-1 w-full h-full min-w-0 overflow-hidden items-stretch">
                <ChatWindow
                  messages={messages}
                  setMessages={setMessages}
                  currentSessionId={currentSessionId}
                  setCurrentSessionId={setCurrentSessionId}
                />
              </div>
            </SidebarInset>

            <TelegramButton />
          </div>
        </SidebarProvider>
      </ThemeProvider>
    </SessionGuard>
  );
};

// --- LOGIC BARU: MEMISAHKAN ROUTE ---
const UserRoutes = () => (
  <Routes>
    <Route path="/" element={<MainApp />} />
    {/* Rute login pengguna sudah ditangani di dalam MainApp */}
  </Routes>
);

const AdminRoutes = () => (
  <Routes>
    <Route
      path="/login"
      element={
        <SessionGuard requiredSessionType="admin">
          <AdminLogin />
        </SessionGuard>
      }
    />
    {/* Tambahkan dukungan path dengan prefix /admin untuk kompatibilitas URL */}
    <Route
      path="/admin/login"
      element={
        <SessionGuard requiredSessionType="admin">
          <AdminLogin />
        </SessionGuard>
      }
    />
    <Route
      path="/dashboard"
      element={
        <SessionGuard requiredSessionType="admin">
          <ProtectedAdminRoute>
            <AdminDashboard />
          </ProtectedAdminRoute>
        </SessionGuard>
      }
    />
    <Route
      path="/admin/dashboard"
      element={
        <SessionGuard requiredSessionType="admin">
          <ProtectedAdminRoute>
            <AdminDashboard />
          </ProtectedAdminRoute>
        </SessionGuard>
      }
    />
    <Route
      path="/upload"
      element={
        <SessionGuard requiredSessionType="admin">
          <ProtectedAdminRoute>
            <AdminUpload />
          </ProtectedAdminRoute>
        </SessionGuard>
      }
    />
    <Route
      path="/admin/upload"
      element={
        <SessionGuard requiredSessionType="admin">
          <ProtectedAdminRoute>
            <AdminUpload />
          </ProtectedAdminRoute>
        </SessionGuard>
      }
    />
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="/admin" element={<Navigate to="/dashboard" replace />} />
  </Routes>
);

// --- LOGIC BARU: Komponen App utama yang memilih router ---
function App() {
  const isAdminDomain = getIsAdminDomain();

  return (
    <AuthProvider>
      <Router>{isAdminDomain ? <AdminRoutes /> : <UserRoutes />}</Router>
    </AuthProvider>
  );
}

export default App;

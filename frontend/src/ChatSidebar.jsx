import React, { useState, useEffect } from "react";
import { getSessions, deleteSession, updateSession } from "./api";
import { useAuth } from "./contexts/AuthContext";
import UserProfile from "./components/UserProfile";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarFooter,
} from "./components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "./components/ui/dropdown-menu";

const ChatSidebar = ({
  currentSessionId,
  onSessionSelect,
  onNewChat,
}) => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingSession, setEditingSession] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  // Load sessions when user changes
  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoading(true);

        // If no user, clear sessions immediately
        if (!user) {
          setSessions([]);
          setLoading(false);
          return;
        }

        const sessionsData = await getSessions();
        setSessions(sessionsData);
      } catch (error) {
        console.error("Error loading sessions:", error);
        // Reset sessions on error
        setSessions([]);
      } finally {
        setLoading(false);
      }
    };

    loadSessions();
  }, [user]); // Only depend on user

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (window.confirm("Apakah Anda yakin ingin menghapus percakapan ini?")) {
      try {
        await deleteSession(sessionId);
        setSessions(sessions.filter((s) => s.session_id !== sessionId));
        if (currentSessionId === sessionId) {
          onNewChat();
        }
      } catch (error) {
        console.error("Error deleting session:", error);
        alert("Gagal menghapus percakapan");
      }
    }
  };

  const handleEditSession = (session, e) => {
    e.stopPropagation();
    setEditingSession(session.session_id);
    setEditTitle(session.title);
  };

  const handleSaveEdit = async (sessionId) => {
    try {
      await updateSession(sessionId, editTitle);
      setSessions(
        sessions.map((s) =>
          s.session_id === sessionId ? { ...s, title: editTitle } : s
        )
      );
      setEditingSession(null);
    } catch (error) {
      console.error("Error updating session:", error);
      alert("Gagal mengubah judul percakapan");
    }
  };

  const handleCancelEdit = () => {
    setEditingSession(null);
    setEditTitle("");
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return "Hari ini";
    } else if (diffDays === 2) {
      return "Kemarin";
    } else if (diffDays <= 7) {
      return `${diffDays - 1} hari lalu`;
    } else {
      return date.toLocaleDateString("id-ID", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    }
  };

  return (
    <Sidebar className="border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
      <SidebarHeader className=" dark:border-gray-100 p-2">
        
        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="w-full   text-gray-900 dark:text-gray-100 px-4 py-1.5 rounded-lg transition-colors duration-200  flex items-center gap-1">
          Chat Baru
        </button>
      </SidebarHeader>

      <SidebarContent className="px-2 py-2">

        {loading ? (
          <div className="p-4 text-center text-gray-600 dark:text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 dark:border-gray-600 mx-auto"></div>
            <p className="mt-2 text-sm">Memuat riwayat...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-600 dark:text-gray-400">
            <p className="text-sm">Belum ada percakapan</p>
            <p className="text-xs mt-1">Mulai chat baru untuk melihat riwayat</p>
          </div>
        ) : (
          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-semibold text-gray-500 dark:text-gray-400 px-2">
              Percakapan Anda
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {sessions.map((session) => (
                  <SidebarMenuItem key={session.session_id}>
                    <div
                      onClick={() => onSessionSelect(session.session_id)}
                      className={`p-3 rounded-lg cursor-pointer transition-all mb-1 group relative flex items-center justify-between ${
                        currentSessionId === session.session_id
                          ? "bg-gray-100 dark:bg-gray-800"
                          : "hover:bg-gray-100 dark:hover:bg-gray-800"
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        {editingSession === session.session_id ? (
                          <div
                            className="flex items-center gap-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                              onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                  handleSaveEdit(session.session_id);
                                } else if (e.key === "Escape") {
                                  handleCancelEdit();
                                }
                              }}
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveEdit(session.session_id)}
                              className="text-green-600 hover:text-green-700"
                            >
                              <svg
                                className="w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              className="text-gray-600 hover:text-gray-700"
                            >
                              <svg
                                className="w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"
                                />
                              </svg>
                            </button>
                          </div>
                        ) : (
                          <>
                            <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate text-sm">
                              {session.title}
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {formatDate(session.updated_at)}
                            </p>
                          </>
                        )}
                      </div>

                      {editingSession !== session.session_id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button
                              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors opacity-0 group-hover:opacity-100"
                              title="Opsi"
                            >
                              <svg
                                className="w-4 h-4"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path d="M12 8c1.1 0 2-0.9 2-2s-0.9-2-2-2-2 0.9-2 2 0.9 2 2 2zm0 2c-1.1 0-2 0.9-2 2s0.9 2 2 2 2-0.9 2-2-0.9-2-2-2zm0 6c-1.1 0-2 0.9-2 2s0.9 2 2 2 2-0.9 2-2-0.9-2-2-2z" />
                              </svg>
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem
                              onClick={(e) => handleEditSession(session, e)}
                              className="cursor-pointer"
                            >
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                />
                              </svg>
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={(e) =>
                                handleDeleteSession(session.session_id, e)
                              }
                              className="cursor-pointer text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400 focus:bg-red-50 dark:focus:bg-red-950"
                            >
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                />
                              </svg>
                              Hapus
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      {/* User Profile Section - Bottom of Sidebar */}
      {user && (
        <SidebarFooter className="border-t border-gray-200 dark:border-gray-800 p-4">
          <UserProfile />
        </SidebarFooter>
      )}
    </Sidebar>
  );
};

export default ChatSidebar;

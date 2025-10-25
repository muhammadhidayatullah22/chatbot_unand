// Use environment variable or fallback to port 8000
const API_BASE_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (window.__ENV__ && window.__ENV__.REACT_APP_BACKEND_URL) ||
  "http://localhost:8001";

console.log("API: Using API_BASE_URL:", API_BASE_URL);
console.log(
  "API: Environment REACT_APP_BACKEND_URL:",
  process.env.REACT_APP_BACKEND_URL
);

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
  };

  console.log("API: Getting auth headers...");
  console.log(
    "API: Token from localStorage:",
    token ? `${token.substring(0, 20)}...` : "null"
  );

  if (token) {
    // Check if token is expired before using it
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Math.floor(Date.now() / 1000);

      console.log("API: Token payload:", payload);
      console.log("API: Current time:", currentTime);
      console.log("API: Token expires at:", payload.exp);

      // If token is expired, don't include it
      if (payload.exp < currentTime) {
        console.log("API: Token expired, not including in headers");
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        return headers;
      }

      headers.Authorization = `Bearer ${token}`;
      console.log("API: Added Authorization header");
    } catch (error) {
      console.error("API: Error checking token:", error);
      // Remove invalid token
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    }
  } else {
    console.log("API: No token found in localStorage");
  }

  console.log("API: Final headers:", headers);
  return headers;
};

export const sendMessageToChatbot = async (query, sessionId = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        query,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Terjadi kesalahan pada server.");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error sending message to chatbot:", error);
    throw error;
  }
};

// Session management functions
export const createSession = async (title = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error creating session:", error);
    throw error;
  }
};

export const getSessions = async () => {
  try {
    console.log("API: Getting sessions from", `${API_BASE_URL}/sessions`);
    const headers = getAuthHeaders();
    console.log("API: Using headers:", headers);

    const response = await fetch(`${API_BASE_URL}/sessions`, {
      headers: headers,
    });

    console.log("API: Sessions response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API: Sessions error response:", errorText);
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log("API: Sessions data received:", data);
    return data;
  } catch (error) {
    console.error("Error getting sessions:", error);
    throw error;
  }
};

export const getSessionMessages = async (sessionId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/sessions/${sessionId}/messages`,
      {
        headers: getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error getting session messages:", error);
    throw error;
  }
};

export const updateSession = async (sessionId, title) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error updating session:", error);
    throw error;
  }
};

export const deleteSession = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error deleting session:", error);
    throw error;
  }
};

import React, { useState, useEffect, useCallback } from "react";
import AdminLayout from "./AdminLayout";
import { useAuth } from "../contexts/AuthContext";

const AdminUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState(null);
  const [knowledgeFiles, setKnowledgeFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const { getAdminAuthHeaders, getAdminAuthHeadersForUpload } = useAuth();

  const getBaseUrl = () =>
    process.env.REACT_APP_BACKEND_URL ||
    (window.__ENV__ && window.__ENV__.REACT_APP_BACKEND_URL) ||
    "http://localhost:8001";

  const fetchKnowledgeFiles = useCallback(async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching knowledge files...");
      console.log("🔑 Auth headers:", getAdminAuthHeaders());

      const response = await fetch(`${getBaseUrl()}/admin/files`, {
        headers: getAdminAuthHeaders(),
      });

      console.log("📡 Files response status:", response.status);

      if (response.ok) {
        const data = await response.json();
        console.log("✅ Knowledge files received:", data);
        setKnowledgeFiles(data);
      } else {
        const errorText = await response.text();
        console.error("❌ Files fetch error:", errorText);
      }
    } catch (error) {
      console.error("❌ Error fetching knowledge files:", error);
    } finally {
      setLoading(false);
    }
  }, [getAdminAuthHeaders]);

  useEffect(() => {
    fetchKnowledgeFiles();
  }, [fetchKnowledgeFiles]);

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const docxFiles = selectedFiles.filter((file) =>
      file.name.toLowerCase().endsWith(".docx")
    );

    if (docxFiles.length !== selectedFiles.length) {
      setMessage({
        type: "error",
        text: "Hanya file .docx yang diperbolehkan",
      });
      return;
    }

    setFiles(docxFiles);
    setMessage(null);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setMessage({
        type: "error",
        text: "Pilih file terlebih dahulu",
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setMessage(null);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${getBaseUrl()}/admin/files/upload`, {
          method: "POST",
          headers: getAdminAuthHeadersForUpload(),
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Upload failed");
        }

        setUploadProgress(((i + 1) / files.length) * 100);
      }

      setMessage({
        type: "success",
        text: `${files.length} file berhasil diupload`,
      });

      setFiles([]);
      document.getElementById("file-input").value = "";

      // Refresh file list
      await fetchKnowledgeFiles();
    } catch (error) {
      console.error("Upload error:", error);
      setMessage({
        type: "error",
        text: error.message || "Upload gagal",
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // Sync function - currently not used, can be re-enabled if sync button is added
  // const handleSync = async () => {
  //   try {
  //     setLoading(true);
  //     setMessage(null);

  //     const response = await fetch(`${getBaseUrl()}/admin/files/sync`, {
  //       method: "POST",
  //       headers: getAdminAuthHeaders(),
  //     });

  //     if (!response.ok) {
  //       const errorText = await response.text();
  //       throw new Error(errorText || "Sync failed");
  //     }

  //     const data = await response.json();
  //     setMessage({
  //       type: "success",
  //       text: `Sinkronisasi selesai: ditambahkan ${data.synced} file${
  //         data.knowledge_base_updated ? ", indeks diperbarui" : ""
  //       }.`,
  //     });
  //     await fetchKnowledgeFiles();
  //   } catch (error) {
  //     console.error("Sync error:", error);
  //     setMessage({ type: "error", text: `Sinkronisasi gagal: ${error.message}` });
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus file ini?")) {
      return;
    }

    try {
      const response = await fetch(`${getBaseUrl()}/admin/files/${fileId}`, {
        method: "DELETE",
        headers: getAdminAuthHeaders(),
      });

      if (response.ok) {
        setMessage({
          type: "success",
          text: "File berhasil dihapus",
        });
        await fetchKnowledgeFiles();
      } else {
        throw new Error("Failed to delete file");
      }
    } catch (error) {
      console.error("Delete error:", error);
      setMessage({
        type: "error",
        text: "Gagal menghapus file",
      });
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Upload File Knowledge Base
          </h3>

          {/* Message */}
          {message && (
            <div
              className={`mb-4 p-4 rounded-md ${
                message.type === "success"
                  ? "bg-green-50 border border-green-200 text-green-800"
                  : "bg-red-50 border border-red-200 text-red-800"
              }`}
            >
              {message.text}
            </div>
          )}

          {/* File Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pilih File (.docx)
            </label>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".docx"
              onChange={handleFileSelect}
              disabled={uploading}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100 disabled:opacity-50"
            />
            <p className="mt-1 text-sm text-gray-500">
              Hanya file .docx yang diperbolehkan. Anda dapat memilih beberapa
              file sekaligus.
            </p>
          </div>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                File yang dipilih:
              </h4>
              <ul className="space-y-1">
                {files.map((file, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-600 flex items-center"
                  >
                    <svg
                      className="w-4 h-4 mr-2 text-green-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {file.name} ({formatFileSize(file.size)})
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Upload Progress */}
          {uploading && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{Math.round(uploadProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? "Uploading..." : "Upload File"}
          </button>


        </div>

        {/* Existing Files */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              File Knowledge Base yang Ada
            </h3>
          </div>

          {loading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nama File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ukuran
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Chunks
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Upload Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {knowledgeFiles.map((file) => (
                    <tr key={file.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <svg
                            className="w-5 h-5 mr-3 text-red-500"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <div className="text-sm font-medium text-gray-900">
                            {file.original_filename}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(file.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {file.processed_chunks}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(file.upload_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleDeleteFile(file.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {knowledgeFiles.length === 0 && (
                <div className="p-6 text-center text-gray-500">
                  Belum ada file yang diupload
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminUpload;

// useLogs.js
import { useState, useEffect, useCallback } from "react";
import axios from "axios";

export const useLogs = (isAuthenticated, fetchToken) => {
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const token = await fetchToken();
      if (!token) {
        setError("No token available");
        return;
      }
      const response = await axios.get("http://localhost:5000/logs", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const extractedLogs = response.data?.logs?.logs || [];
      if (Array.isArray(extractedLogs)) {
        setLogs(extractedLogs);
        if (extractedLogs.length > 0) {
          const keys = Object.keys(extractedLogs[0]);
          setColumns(keys);
        }
      }
    } catch (error) {
      setError("Error fetching logs: " + error.message);
    } finally {
      setLoading(false);
    }
  }, [fetchToken]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchLogs();
    }
  }, [isAuthenticated, fetchLogs]);

  return { logs, columns, error, loading };
};

import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";

export const useLogs = (isAuthenticated, fetchToken) => {
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const hasFetchedLogs = useRef(false); // Track if data has already been fetched

  // Use a ref to track if the request is currently in progress
  const isFetching = useRef(false);

  const fetchLogs = useCallback(async () => {
    // Ensure we only fetch once unless necessary
    if (hasFetchedLogs.current || isFetching.current) return;

    setLoading(true);
    isFetching.current = true; // Set the fetching state to true to prevent multiple API calls

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

      hasFetchedLogs.current = true; // Mark that data has been fetched
    } catch (error) {
      setError("Error fetching logs: " + error.message);
    } finally {
      setLoading(false);
      isFetching.current = false; // Reset fetching state after request completes
    }
  }, [fetchToken]);

  useEffect(() => {
    // Only fetch logs when authenticated and if data hasn't been fetched yet
    if (isAuthenticated && !hasFetchedLogs.current) {
      fetchLogs();
    }
  }, [isAuthenticated, fetchLogs]);

  return { logs, columns, error, loading };
};

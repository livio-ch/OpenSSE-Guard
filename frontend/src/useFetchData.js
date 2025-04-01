import { useState, useEffect, useCallback } from "react";
import axios from "axios";

export const useFetchData = (isAuthenticated, fetchToken, endpoint) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const token = await fetchToken();
      if (!token) {
        setError("No token available");
        return;
      }
      const response = await axios.get(endpoint, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const extractedData = response.data?.data || [];  // Adjust depending on your API's response structure
      if (Array.isArray(extractedData)) {
        setData(extractedData);
        if (extractedData.length > 0) {
          const keys = Object.keys(extractedData[0]);
          setColumns(keys);
        }
      }
    } catch (error) {
      setError("Error fetching data: " + error.message);
    } finally {
      setLoading(false);
    }
  }, [fetchToken, endpoint]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated, fetchData]);

  return { data, columns, error, loading };
};

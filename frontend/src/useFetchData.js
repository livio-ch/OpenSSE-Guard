import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";

// Simplified version to handle flexible API responses
export const useFetchData = (isAuthenticated, fetchToken, apiUrl) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const hasFetchedData = useRef(false); // Track if data has already been fetched
  const isFetching = useRef(false); // Prevent multiple fetch calls in parallel

  const fetchData = useCallback(async () => {
    // Prevent multiple API calls if data is already fetched or is currently being fetched
    if (hasFetchedData.current || isFetching.current) return;

    setLoading(true);
    isFetching.current = true; // Set the fetching state to true

    try {
      const token = await fetchToken();
      if (!token) {
        setError("No token available");
        return;
      }

      const response = await axios.get(apiUrl, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Simplified extraction of data - Find the first array in the response
      const findArray = (obj) => {
        if (Array.isArray(obj)) return obj; // Return array if found
        if (typeof obj === 'object' && obj !== null) {
          for (let key in obj) {
            const result = findArray(obj[key]);
            if (result) return result; // Return the first array found
          }
        }
        return null; // Return null if no array is found
      };

      // Extract data using the findArray function
      const extractedData = findArray(response.data) || [];

      // If data is an array, update state with the data and column names
      if (Array.isArray(extractedData)) {
        setData(extractedData);
        if (extractedData.length > 0) {
          const keys = Object.keys(extractedData[0]);
          setColumns(keys); // Assuming the first object will provide the column headers
        }
      }

      hasFetchedData.current = true; // Mark data as fetched
    } catch (error) {
      setError("Error fetching data: " + error.message);
    } finally {
      setLoading(false);
      isFetching.current = false; // Reset fetching state after request completes
    }
  }, [fetchToken, apiUrl]);

  useEffect(() => {
    if (isAuthenticated && !hasFetchedData.current) {
      fetchData();
    }
  }, [isAuthenticated, fetchData]);

  return { data, columns, error, loading };
};

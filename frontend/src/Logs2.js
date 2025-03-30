import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAuth0 } from "@auth0/auth0-react";

function Logs2() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0(); // Get Auth0 token
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [filterText, setFilterText] = useState(""); // State for the free text filter
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false); // Loading state
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" }); // Sorting state

  useEffect(() => {
    if (isAuthenticated) {
      // Function to fetch logs from the API
      const fetchLogs = async () => {
        setLoading(true); // Set loading to true when fetching data
        try {
          // Get the token from Auth0
          const token = await getAccessTokenSilently();
          if (!token) {
            setError("No token available");
            return;
          }

          // Send the token with the request
          const response = await axios.get("http://localhost:5000/logs", {
            headers: {
              'Authorization': `Bearer ${token}`, // Attach token here
            },
          });

          // Handle the API response
          const extractedLogs = response.data?.logs?.logs || [];
          if (Array.isArray(extractedLogs)) {
            setLogs(extractedLogs);
            if (extractedLogs.length > 0) {
              const firstLog = extractedLogs[0];
              setColumns(Object.keys(firstLog)); // Dynamically set columns
              setFilters(Object.fromEntries(Object.keys(firstLog).map(key => [key, ""])));
            }
          }
        } catch (error) {
          setError("Error fetching logs: " + error.message);
          console.error("Error fetching logs:", error);
        } finally {
          setLoading(false); // Set loading to false after the data is fetched
        }
      };

      fetchLogs();
    }
  }, [getAccessTokenSilently, isAuthenticated]);

  const checkIfValueMatchesFilter = (value, filterValue) => {
    if (value === null || value === undefined) return false;

    // Convert both value and filterValue to lowercase for case-insensitive matching
    const lowerValue = value.toString().toLowerCase();
    const lowerFilterValue = filterValue.toLowerCase();

    // Handle wildcard: replace * with .* for regex matching
    const regex = new RegExp(lowerFilterValue.replace(/\*/g, ".*"));

    // Check if the value matches the filter (case-insensitive and wildcard supported)
    return regex.test(lowerValue);
  };

  const getValueFromObject = (obj, path) => {
    const keys = path.split('.'); // Split the path by dots for nested fields
    let value = obj;
    for (let key of keys) {
      if (value && value[key] !== undefined) {
        value = value[key];
      } else {
        return undefined; // Return undefined if the path does not exist
      }
    }
    return value;
  };

  const applyFilters = (logs) => {
    const filterArray = filterText.split(/\s+(AND|OR)\s+/i); // Split by AND/OR (case insensitive)
    let filteredLogs = [...logs];

    // Parse each term in the filter and apply it
    let parsedFilterArray = [];

    filterArray.forEach((filterTerm) => {
      const match = filterTerm.match(/([a-zA-Z0-9_\.]+)\s*(==|!=|>|<)\s*(.*)/); // Match the pattern: column operator value
      if (match) {
        const [_, column, operator, value] = match;
        parsedFilterArray.push({ column: column.toLowerCase(), operator, value }); // Normalize column name to lowercase
      }
    });

    // Apply the parsed filters to the logs
    parsedFilterArray.forEach(({ column, operator, value }) => {
      filteredLogs = filteredLogs.filter((log) => {
        const logValue = getValueFromObject(log, column); // Get the value from the log based on the column path

        // If no value found in the log, skip it
        if (logValue === undefined) return false;

        // Convert both log value and filter value to number if possible for numeric comparison
        const parsedLogValue = isNaN(logValue) ? logValue : Number(logValue);
        const parsedFilterValue = isNaN(value) ? value : Number(value);

        // Compare the values based on the operator
        if (operator === "==") {
          return parsedLogValue == parsedFilterValue; // Loose comparison to handle type coercion
        } else if (operator === "!=") {
          return parsedLogValue != parsedFilterValue;
        } else if (operator === ">") {
          return parsedLogValue > parsedFilterValue;
        } else if (operator === "<") {
          return parsedLogValue < parsedFilterValue;
        }
        return false;
      });
    });

    return filteredLogs;
  };

  const handleFilterTextChange = (e) => {
    setFilterText(e.target.value);
  };

  const clearFilters = () => {
    setFilterText("");
  };

  const filteredLogs = applyFilters(logs);

  const handleSort = (column) => {
    const direction = sortConfig.direction === "asc" ? "desc" : "asc"; // Toggle direction
    setSortConfig({ key: column, direction: direction });
  };

  const sortLogs = (logs) => {
    if (sortConfig.key === null) return logs; // If no column is selected for sorting, return the original logs

    const sortedLogs = [...logs];
    const { key, direction } = sortConfig;

    // Sort by the selected column and direction
    sortedLogs.sort((a, b) => {
      const aValue = getValueFromObject(a, key);
      const bValue = getValueFromObject(b, key);

      // Handle sorting for different types (strings, numbers, etc.)
      if (aValue < bValue) return direction === "asc" ? -1 : 1;
      if (aValue > bValue) return direction === "asc" ? 1 : -1;
      return 0;
    });

    return sortedLogs;
  };

  const sortedLogs = sortLogs(filteredLogs);

  const formatCell = (value) => {
    if (value === null || value === undefined) return "N/A";

    // If the value is an object, format it accordingly
    if (typeof value === "object" && value !== null) {
      return Object.entries(value).map(([subKey, subValue]) => {
        // Truncate the subKey if it's too long
        const truncatedSubKey = subKey.length > 100 ? subKey.substring(0, 100) + "..." : subKey;

        if (typeof subValue === "object") {
          return (
            <div key={subKey} title={JSON.stringify(subValue)}>
              {truncatedSubKey}: [object]
            </div>
          );
        }

        // Truncate the subValue if it's a string and too long
        const truncatedSubValue = typeof subValue === "string" && subValue.length > 100 ? subValue.substring(0, 100) + "..." : subValue;

        return (
          <div key={subKey} title={subValue}>
            <strong>{truncatedSubKey}:</strong> {truncatedSubValue}
          </div>
        );
      });
    }

    return value;
  };

  const handleCellDoubleClick = (column, value) => {
    let filter = '';

    // Check if the value is an object
    if (typeof value === 'object' && value !== null) {
      // If it's an object, recursively go through its keys and add to filter
      filter = Object.entries(value)
        .map(([key, subValue]) => {
          // If the subValue is also an object, handle it recursively
          return `${column}.${key} == ${subValue}`;
        })
        .join(' OR ');  // If you want "OR" between nested keys
    } else {
      // Otherwise, just add the column and value for the filter
      filter = `${column} == ${value}`;
    }

    // Update filterText directly
    setFilterText((prevFilterText) => {
      if (prevFilterText.trim()) {
        return `${prevFilterText} AND ${filter}`;
      } else {
        return filter;
      }
    });
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Logs</h2>

      {/* Filter Input */}
      <div className="mb-4">
        <input
          type="text"
          value={filterText}
          onChange={handleFilterTextChange}
          style={{ width: "600px" }}  // Increased width for better visibility
          className="p-2 border rounded"
          placeholder="Enter filter (e.g., category == error OR level > 3)"
        />
        <button
          onClick={() => setFilterText(filterText)}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Filter
        </button>
        <button
          onClick={clearFilters}
          className="mt-2 px-4 py-2 bg-gray-500 text-white rounded ml-2"
        >
          Clear Filter
        </button>
      </div>

      {/* Loading Spinner */}
      {loading && <p className="text-gray-500 mt-4">Loading...</p>}

      {/* Error Message */}
      {error && <p className="text-red-500">{error}</p>}

      {logs.length === 0 && !loading ? (
        <p className="text-gray-500 mt-4">No logs available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                {columns.map((key, index) => (
                  <th
                    key={index}
                    className="border p-2 cursor-pointer"
                    onClick={() => handleSort(key)}
                  >
                    {key.toLowerCase().replace("_", " ").toUpperCase()}
                    {/* Display sort arrow */}
                    {sortConfig.key === key && (
                      <span>{sortConfig.direction === "asc" ? " ↑" : " ↓"}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedLogs.map((log, index) => (
                <tr key={index} className="border">
                  {columns.map((key, idx) => (
                    <td
                      key={idx}
                      className="border p-2"
                      onDoubleClick={() => handleCellDoubleClick(key, log[key])}
                    >
                      {formatCell(log[key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Logs2;

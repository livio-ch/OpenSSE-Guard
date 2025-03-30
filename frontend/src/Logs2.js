import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAuth0 } from "@auth0/auth0-react";

import FilterInput from "./components/FilterInput";

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

          console.log("API Response:", response.data); // Log the response

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
    if (!filterText.trim()) {
      return logs; // If filterText is empty, return all logs
    }

    const filterArray = filterText.split(/\s+(AND|OR|XOR|NAND)\s+/i); // Split by AND/OR/XOR/NAND (case insensitive)
    let parsedFilterArray = [];
    let currentOperator = 'AND'; // Default operator

    // Parse filter text into conditions
    filterArray.forEach((filterTerm) => {
      if (filterTerm.toUpperCase() === 'AND' || filterTerm.toUpperCase() === 'OR' || filterTerm.toUpperCase() === 'XOR' || filterTerm.toUpperCase() === 'NAND') {
        currentOperator = filterTerm.toUpperCase();
      } else {
        const match = filterTerm.match(/([a-zA-Z0-9_\.]+)\s*(==|!=|>|<)\s*(.*)/);
        if (match) {
          const [_, column, operator, value] = match;
          parsedFilterArray.push({ column: column.toLowerCase(), operator, value, currentOperator });
        }
      }
    });

    return logs.filter((log) => {
      let result = parsedFilterArray[0]?.currentOperator === 'AND' ? true : false;

      parsedFilterArray.forEach(({ column, operator, value, currentOperator }) => {
        // Safely get the value from the log
        const logValue = getValueFromObject(log, column);

        if (logValue === undefined || logValue === null) {
          // If the field doesn't exist, skip the filter or handle accordingly
          result = currentOperator === "AND" ? false : result; // If using AND, the filter fails if any field is missing
          return;
        }

        const parsedLogValue = isNaN(logValue) ? logValue : Number(logValue);
        const parsedFilterValue = isNaN(value) ? value : Number(value);

        let conditionMet = false;
        if (operator === "==") conditionMet = parsedLogValue == parsedFilterValue;
        else if (operator === "!=") conditionMet = parsedLogValue != parsedFilterValue;
        else if (operator === ">") conditionMet = parsedLogValue > parsedFilterValue;
        else if (operator === "<") conditionMet = parsedLogValue < parsedFilterValue;

        if (currentOperator === "AND") {
          result = result && conditionMet;
        } else if (currentOperator === "OR") {
          result = result || conditionMet;
        } else if (currentOperator === "XOR") {
          result = (result ? 1 : 0) ^ (conditionMet ? 1 : 0) ? true : false;
        } else if (currentOperator === "NAND") {
          result = !(result && conditionMet);
        }
      });

      return result;
    });
  };


  const handleFilterTextChange = (e) => {
    console.log("Filter Text Before Update:", filterText);  // Log the previous filter text
    setFilterText(e.target.value);
  };

  const clearFilters = () => {
    setFilterText("");
  };

  const filteredLogs = applyFilters(logs);
  console.log("Filtered Logs:", filteredLogs);  // Log filtered logs

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
  console.log("Sorted Logs:", sortedLogs);  // Log sorted logs

  const formatCell = (value) => {
    if (value === null || value === undefined) return "N/A";

    // If the value is an object, format it accordingly
    if (typeof value === "object" && value !== null) {
      console.log("Formatting Object:", value);  // Log the object being formatted
      return Object.entries(value).map(([subKey, subValue]) => {
        const truncatedSubKey = subKey.length > 100 ? subKey.substring(0, 100) + "..." : subKey;
        if (typeof subValue === "object") {
          return (
            <div key={subKey} title={JSON.stringify(subValue)}>
              {truncatedSubKey}: [object]
            </div>
          );
        }

        const truncatedSubValue = typeof subValue === "string" && subValue.length > 100 ? subValue.substring(0, 100) + "..." : subValue;
        return (
          <div key={subKey} title={subValue}>
            <strong>{truncatedSubKey}:</strong> {truncatedSubValue}
          </div>
        );
      });
    }

    console.log("Formatting Value:", value);  // Log non-object value being formatted
    return value;
  };

  const handleCellDoubleClick = (column, value) => {
    let filter = '';

    // Check if the value is an object
    if (typeof value === 'object' && value !== null) {
      console.log("Double Clicked Object:", value);  // Log the object being double-clicked
      filter = Object.entries(value)
        .map(([key, subValue]) => `${column}.${key} == ${subValue}`)
        .join(' OR ');
    } else {
      console.log("Double Clicked Value:", value);  // Log the value being double-clicked
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
        <FilterInput filterText={filterText} setFilterText={setFilterText} clearFilters={clearFilters} />
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

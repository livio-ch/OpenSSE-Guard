import { useEffect, useState } from "react";
import axios from "axios";

function Logs() {
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    axios.get("http://localhost:5000/logs")
      .then(response => {
        console.log("API Response:", response.data); // Debugging
        const extractedLogs = response.data?.logs?.logs || [];
        if (Array.isArray(extractedLogs)) {
          setLogs(extractedLogs);
          if (extractedLogs.length > 0) {
            const firstLog = extractedLogs[0];
            setColumns(Object.keys(firstLog)); // Dynamically set columns
            setFilters(Object.fromEntries(Object.keys(firstLog).map(key => [key, ""])));
          }
        }
      })
      .catch(error => console.error("Error fetching logs:", error));
  }, []);

  // Helper function to check if a nested value matches the filter
  const checkIfValueMatchesFilter = (value, filterValue) => {
    if (value === null || value === undefined) return false;

    // If the value is a string or number, check if it includes the filter
    if (typeof value === "string" || typeof value === "number") {
      return value.toString().toLowerCase().includes(filterValue.toLowerCase());
    }

    // If the value is an object, check its properties recursively
    if (typeof value === "object" && value !== null) {
      for (let key in value) {
        if (checkIfValueMatchesFilter(value[key], filterValue)) {
          return true;
        }
      }
    }

    return false;
  };

  // Function to get unique filter values for a given column, including nested object keys
  const getUniqueValues = (key, logsToFilter) => {
    let values = [];

    logsToFilter.forEach(log => {
      const value = log[key];

      if (value === null || value === undefined) return;

      if (typeof value === "object" && value !== null) {
        // If the value is an object, we check its keys and values for uniqueness
        Object.entries(value).forEach(([subKey, subValue]) => {
          if (typeof subValue === "string" || typeof subValue === "number") {
            values.push(subValue);
          }
        });
      } else {
        values.push(value);
      }
    });

    // Remove duplicates and sort the values alphabetically
    return [...new Set(values)].filter(value => value !== "").sort((a, b) => a.toString().localeCompare(b.toString()));
  };

  // Handle filter changes
  const handleFilterChange = (e, column) => {
    setFilters({ ...filters, [column]: e.target.value });
  };

  // Apply filters to the logs
  const filteredLogs = logs.filter(log =>
    Object.keys(filters).every(key => {
      const filterValue = filters[key].toLowerCase();
      const logValue = log[key];

      // If the filter is empty, show the log
      if (filterValue === "") return true;

      // Apply recursive check to handle nested JSON objects
      return checkIfValueMatchesFilter(logValue, filterValue);
    })
  );

  // Format the cell value for display
  const formatCell = (value) => {
    if (value === null || value === undefined) {
      return "N/A"; // Default value if the cell is null or undefined
    }
    if (typeof value === "object" && value !== null) {
      // If the value is a JSON object, unpack and display its properties
      return Object.entries(value).map(([subKey, subValue]) => (
        <div key={subKey}>
          <strong>{subKey}:</strong> {subValue}
        </div>
      ));
    }
    return value; // Return the value as is if it's not an object
  };

  // Clear all filters
  const clearFilters = () => {
    const resetFilters = Object.fromEntries(Object.keys(filters).map(key => [key, ""]));
    setFilters(resetFilters);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Logs</h2>

      {/* Clear Filters Button */}
      <button
        onClick={clearFilters}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Clear Filters
      </button>

      {logs.length === 0 ? (
        <p className="text-gray-500 mt-4">No logs available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                {columns.map((key, index) => (
                  <th key={index} className="border p-2">
                    {key.replace("_", " ").toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                {/* Filter dropdowns for each column */}
                {columns.map((key, index) => (
                  <td key={index} className="border p-2">
                    <select
                      value={filters[key] || ""}
                      onChange={(e) => handleFilterChange(e, key)}
                      className="p-1 w-full text-sm border rounded"
                    >
                      <option value="">-- {key.replace("_", " ").toUpperCase()} --</option>
                      {getUniqueValues(key, filteredLogs).map((value, idx) => {
                        let displayValue = value.length > 30 ? value.substring(0, 30) + "..." : value;
                        return (
                          <option key={idx} value={value}>
                            {displayValue}
                          </option>
                        );
                      })}
                    </select>
                  </td>
                ))}
              </tr>
              {filteredLogs.map((log, index) => (
                <tr key={index} className="border">
                  {columns.map((key, idx) => (
                    <td key={idx} className="border p-2">
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

export default Logs;

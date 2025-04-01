import React, { useEffect, useState, useMemo, useCallback } from "react";
import axios from "axios";
import { useAuth } from "./useAuth";
import FilterInput from "./components/FilterInput";

function Logs2() {
  const { fetchToken, isAuthenticated } = useAuth();
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [filterText, setFilterText] = useState(""); // State for the free text filter
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false); // Loading state
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" }); // Sorting state

  // Fetch logs only when isAuthenticated changes to true.
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
          const firstLog = extractedLogs[0];
          const keys = Object.keys(firstLog);
          setColumns(keys);
          setFilters(Object.fromEntries(keys.map((key) => [key, ""])));
        }
      }
    } catch (error) {
      setError("Error fetching logs: " + error.message);
      console.error("Error fetching logs:", error);
    } finally {
      setLoading(false);
    }
  }, [fetchToken]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchLogs();
    }
  }, [isAuthenticated, fetchLogs]);

  // Utility function to get nested values from an object.
  const getValueFromObject = useCallback((obj, path) => {
    return path.split(".").reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), obj);
  }, []);

  // Apply filters based on filterText
  const applyFilters = useCallback(
    (logs) => {
      if (!filterText.trim()) {
        return logs; // Return all logs if filterText is empty.
      }

      // Split filterText by operators AND, OR, XOR, NAND.
      const filterArray = filterText.split(/\s+(AND|OR|XOR|NAND)\s+/i);
      const parsedFilterArray = [];
      let currentOperator = "AND";

      filterArray.forEach((term) => {
        const upperTerm = term.toUpperCase();
        if (["AND", "OR", "XOR", "NAND"].includes(upperTerm)) {
          currentOperator = upperTerm;
        } else {
          const match = term.match(/([a-zA-Z0-9_\.]+)\s*(==|!=|>|<)\s*(.*)/);
          if (match) {
            const [, column, operator, value] = match;
            parsedFilterArray.push({ column: column.toLowerCase(), operator, value, currentOperator });
          }
        }
      });

      return logs.filter((log) => {
        // Initialize result based on the first operator.
        let result = parsedFilterArray[0]?.currentOperator === "AND" ? true : false;
        parsedFilterArray.forEach(({ column, operator, value, currentOperator }) => {
          const logValue = getValueFromObject(log, column);
          if (logValue === undefined || logValue === null) {
            // For AND, missing fields cause filter to fail.
            result = currentOperator === "AND" ? false : result;
            return;
          }
          const parsedLogValue = isNaN(logValue) ? logValue : Number(logValue);
          const parsedFilterValue = isNaN(value) ? value : Number(value);
          let conditionMet = false;
          if (operator === "==") conditionMet = parsedLogValue == parsedFilterValue;
          else if (operator === "!=") conditionMet = parsedLogValue != parsedFilterValue;
          else if (operator === ">") conditionMet = parsedLogValue > parsedFilterValue;
          else if (operator === "<") conditionMet = parsedLogValue < parsedFilterValue;

          if (currentOperator === "AND") result = result && conditionMet;
          else if (currentOperator === "OR") result = result || conditionMet;
          else if (currentOperator === "XOR") result = (result ? 1 : 0) ^ (conditionMet ? 1 : 0) ? true : false;
          else if (currentOperator === "NAND") result = !(result && conditionMet);
        });
        return result;
      });
    },
    [filterText, getValueFromObject]
  );

  // Memoize filtered logs so they are recomputed only when logs or filterText changes.
  const filteredLogs = useMemo(() => applyFilters(logs), [logs, applyFilters]);

  // Handlers for filter input
  const handleFilterTextChange = useCallback((e) => {
    console.log("Filter Text Before Update:", filterText);
    setFilterText(e.target.value);
  }, [filterText]);

  const clearFilters = useCallback(() => {
    setFilterText("");
  }, []);

  // Sorting functions
  const handleSort = useCallback((column) => {
    setSortConfig((prev) => ({
      key: column,
      direction: prev.key === column && prev.direction === "asc" ? "desc" : "asc",
    }));
  }, []);

  const sortLogs = useCallback(
    (logs) => {
      if (!sortConfig.key) return logs;
      const sorted = [...logs].sort((a, b) => {
        const aValue = getValueFromObject(a, sortConfig.key);
        const bValue = getValueFromObject(b, sortConfig.key);
        if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
      return sorted;
    },
    [sortConfig, getValueFromObject]
  );

  // Memoize sorted logs based on filteredLogs and sortConfig.
  const sortedLogs = useMemo(() => sortLogs(filteredLogs), [filteredLogs, sortLogs]);

  // Extract field options for the FilterInput component.
  const extractFieldOptions = useCallback((logs) => {
    const fieldOptions = {};

    const extractFieldsRecursively = (obj, prefix = "") => {
      Object.keys(obj).forEach((key) => {
        const fullPath = prefix ? `${prefix}.${key}` : key;
        const value = obj[key];
        if (typeof value === "object" && value !== null) {
          extractFieldsRecursively(value, fullPath);
        } else {
          if (!fieldOptions[fullPath]) {
            fieldOptions[fullPath] = new Set();
          }
          fieldOptions[fullPath].add(value);
        }
      });
    };

    logs.forEach((log) => extractFieldsRecursively(log));
    return Object.fromEntries(Object.entries(fieldOptions).map(([key, value]) => [key, [...value]]));
  }, []);

  const fieldOptions = useMemo(() => extractFieldOptions(logs), [logs]);

  // Format a cell based on its value.
  const formatCell = useCallback((value) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "object" && value !== null) {
      console.log("Formatting Object:", value);
      return Object.entries(value).map(([subKey, subValue]) => {
        const truncatedSubKey = subKey.length > 100 ? subKey.substring(0, 100) + "..." : subKey;
        if (typeof subValue === "object") {
          return (
            <div key={subKey} title={JSON.stringify(subValue)}>
              {truncatedSubKey}: [object]
            </div>
          );
        }
        const truncatedSubValue =
          typeof subValue === "string" && subValue.length > 100
            ? subValue.substring(0, 100) + "..."
            : subValue;
        return (
          <div key={subKey} title={subValue}>
            <strong>{truncatedSubKey}:</strong> {truncatedSubValue}
          </div>
        );
      });
    }
    console.log("Formatting Value:", value);
    return value;
  }, []);

  // On double click, update the filter text by appending a filter based on the cell value.
  const handleCellDoubleClick = useCallback((column, value) => {
    let filter = "";
    if (typeof value === "object" && value !== null) {
      console.log("Double Clicked Object:", value);
      filter = Object.entries(value)
        .map(([key, subValue]) => `${column}.${key} == ${subValue}`)
        .join(" OR ");
    } else {
      console.log("Double Clicked Value:", value);
      filter = `${column} == ${value}`;
    }
    setFilterText((prev) => (prev.trim() ? `${prev} AND ${filter}` : filter));
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Logs</h2>

      {/* Filter Input */}
      <div className="mb-4">
        <FilterInput
          filterText={filterText}
          setFilterText={setFilterText}
          clearFilters={clearFilters}
          fieldOptions={fieldOptions}
        />
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
                {columns.map((col, index) => (
                  <th
                    key={index}
                    className="border p-2 cursor-pointer"
                    onClick={() => handleSort(col)}
                  >
                    {col.toLowerCase().replace("_", " ").toUpperCase()}
                    {sortConfig.key === col && (
                      <span>{sortConfig.direction === "asc" ? " ↑" : " ↓"}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedLogs.map((log, index) => (
                <tr key={index} className="border">
                  {columns.map((col, idx) => (
                    <td
                      key={idx}
                      className="border p-2"
                      onDoubleClick={() => handleCellDoubleClick(col, log[col])}
                    >
                      {formatCell(log[col])}
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

import React, { useState, useMemo, useCallback } from "react";
import FilterInput from "./components/FilterInput";
import LogsTable from "./LogsTable";
import { useAuth } from "./useAuth";
import { useFetchData } from "./useFetchData";
import { getValueFromObject, applyFilters, sortLogs, extractFieldOptions } from "./logUtils";

function Logs2() {
  const { fetchToken, isAuthenticated } = useAuth();
  const { data: logs, columns, error, loading } = useFetchData(
    isAuthenticated,
    fetchToken,
    "http://localhost:5000/logs" // The URL for logs
  );

  const [filterText, setFilterText] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });

  // Compute filtered logs based on the filterText.
  const filteredLogs = useMemo(
    () => applyFilters(logs, filterText, getValueFromObject),
    [logs, filterText]
  );

  // Compute sorted logs based on the sort configuration.
  const sortedLogs = useMemo(
    () => sortLogs(filteredLogs, sortConfig, getValueFromObject),
    [filteredLogs, sortConfig]
  );

  // Compute field options for the FilterInput component.
  const fieldOptions = useMemo(() => extractFieldOptions(logs), [logs]);

  // Handlers for filter input changes.
  const handleFilterTextChange = useCallback((e) => {
    setFilterText(e.target.value);
  }, []);

  const clearFilters = useCallback(() => {
    setFilterText("");
  }, []);

  // Handler to update the sort configuration when a column header is clicked.
  const handleSort = useCallback((column) => {
    setSortConfig((prev) => ({
      key: column,
      direction: prev.key === column && prev.direction === "asc" ? "desc" : "asc",
    }));
  }, []);

  // Update filterText based on double-clicked cell value.
  const handleCellDoubleClick = useCallback((column, value) => {
    let filter = "";
    if (typeof value === "object" && value !== null) {
      filter = Object.entries(value)
        .map(([key, subValue]) => `${column}.${key} == ${subValue}`)
        .join(" AND ");
    } else {
      filter = `${column} == ${value}`;
    }
    setFilterText((prev) => (prev.trim() ? `${prev} AND ${filter}` : filter));
  }, []);

  // Format a cell based on its value.
  const formatCell = useCallback((value) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "object" && value !== null) {
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
    return value;
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
          onChange={handleFilterTextChange}
        />
      </div>

      {/* Loading & Error States */}
      {loading && <p className="text-gray-500 mt-4">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {logs.length === 0 && !loading ? (
        <p className="text-gray-500 mt-4">No logs available.</p>
      ) : (
        <LogsTable
          columns={columns}
          sortedLogs={sortedLogs}
          handleSort={handleSort}
          sortConfig={sortConfig}
          handleCellDoubleClick={handleCellDoubleClick}
          formatCell={formatCell}
        />
      )}
    </div>
  );
}

export default Logs2;

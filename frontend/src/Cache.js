import React, { useState, useMemo, useCallback } from "react";
import FilterInput from "./components/FilterInput";
import LogsTable from "./LogsTable";
import { useAuth } from "./useAuth";
import { useFetchData } from "./useFetchData";
import { getValueFromObject, applyFilters, sortLogs, extractFieldOptions } from "./logUtils";

function Cache() {
  const { fetchToken, isAuthenticated } = useAuth();

  // Use useFetchData hook to fetch logs data
  const { data: logs, columns, error, loading } = useFetchData(
    isAuthenticated,
    fetchToken,
    "http://localhost:5000/cache" // The URL for logs
  );

  const [filterText, setFilterText] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });

  // Compute filtered logs based on the filterText
  const filteredLogs = useMemo(
    () => applyFilters(logs, filterText, getValueFromObject),
    [logs, filterText]
  );

  // Compute sorted logs based on the sort configuration
  const sortedLogs = useMemo(
    () => sortLogs(filteredLogs, sortConfig, getValueFromObject),
    [filteredLogs, sortConfig]
  );

  // Compute field options for the FilterInput component
  const fieldOptions = useMemo(() => extractFieldOptions(logs), [logs]);

  // Handlers for filter input changes
  const handleFilterTextChange = useCallback((e) => {
    setFilterText(e.target.value);
  }, []);

  const clearFilters = useCallback(() => {
    setFilterText("");
  }, []);

  // Handler to update the sort configuration when a column header is clicked
  const handleSort = useCallback((column) => {
    setSortConfig((prev) => ({
      key: column,
      direction: prev.key === column && prev.direction === "asc" ? "desc" : "asc",
    }));
  }, []);

  // Update filterText based on double-clicked cell value
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

  // Format a cell based on its value
  const formatCell = useCallback((value) => {
    if (value === null || value === undefined) return "N/A";

    if (typeof value === "object") {
      return <NestedObjectRenderer objectData={value} />;
    }

    return value;
  }, []);

  const NestedObjectRenderer = ({ objectData }) => {
    const [expandedKeys, setExpandedKeys] = useState({});

    const toggleExpand = (key) => {
      setExpandedKeys((prev) => ({
        ...prev,
        [key]: !prev[key],
      }));
    };

    return Object.entries(objectData).map(([subKey, subValue]) => {
      const truncatedSubKey = subKey.length > 100 ? subKey.substring(0, 100) + "..." : subKey;

      if (typeof subValue === "object") {
        return (
          <div key={subKey} style={{ marginLeft: "10px" }}>
            <span
              onClick={() => toggleExpand(subKey)}
              style={{ cursor: "pointer", color: "blue", textDecoration: "underline" }}
              title={JSON.stringify(subValue)}
            >
              {truncatedSubKey}: {expandedKeys[subKey] ? "[collapse]" : "[expand]"}
            </span>
            {expandedKeys[subKey] && (
              <div style={{ marginLeft: "10px", borderLeft: "1px solid gray", paddingLeft: "5px" }}>
                <NestedObjectRenderer objectData={subValue} />
              </div>
            )}
          </div>
        );
      }

      const truncatedSubValue =
        typeof subValue === "string" && subValue.length > 100
          ? subValue.substring(0, 100) + "..."
          : subValue;

      return (
        <div key={subKey} style={{ marginLeft: "10px" }} title={subValue}>
          <strong>{truncatedSubKey}:</strong> {truncatedSubValue}
        </div>
      );
    });
  };




  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">API Cache</h2>

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
        <p className="text-gray-500 mt-4">No cache available.</p>
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

export default Cache;

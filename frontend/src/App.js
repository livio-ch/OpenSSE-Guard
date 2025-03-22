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
            setColumns(Object.keys(extractedLogs[0])); // Dynamically set columns
            setFilters(Object.fromEntries(Object.keys(extractedLogs[0]).map(key => [key, ""])));
          }
        }
      })
      .catch(error => console.error("Error fetching logs:", error));
  }, []);

  // Extract unique values for dropdowns
  const getUniqueValues = (key) => {
    return [...new Set(logs.map(log => (log[key] ? JSON.stringify(log[key]) : "")))].filter(value => value !== "");
  };

  const handleFilterChange = (e, column) => {
    setFilters({ ...filters, [column]: e.target.value });
  };

  const filteredLogs = logs.filter(log =>
    Object.keys(filters).every(key =>
      filters[key] === "" || JSON.stringify(log[key]) === filters[key]
    )
  );

  // Format cell content
  const formatCell = (value) => {
    if (typeof value === "object" && value !== null) {
      return JSON.stringify(value); // Convert objects to JSON
    }
    return value;
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Logs</h2>
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
                    <select
                      value={filters[key] || ""}
                      onChange={(e) => handleFilterChange(e, key)}
                      className="mt-1 p-1 w-full text-sm border rounded"
                    >
                      <option value="">All</option>
                      {getUniqueValues(key).map((value, idx) => {
                        let displayValue = value.length > 30 ? value.substring(0, 30) + "..." : value;
                        return (
                          <option key={idx} value={value}>
                            {displayValue}
                          </option>
                        );
                      })}
                    </select>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
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

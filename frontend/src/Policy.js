import React, { useState, useEffect } from "react";
import axios from "axios";

const Policy = () => {
  const [table, setTable] = useState("blocked_urls"); // Default table
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});
  const [columns, setColumns] = useState([]);

  const tableOptions = [
    { label: "Blocked URLs", value: "blocked_urls" },
    { label: "Blocked Files", value: "blocked_files" },
    { label: "Blocked MIME Types", value: "blocked_mimetypes" },
    { label: "Redirect URLs", value: "redirect_urls" },
    { label: "TLS Excluded Hosts", value: "tls_excluded_hosts" },
  ];

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`http://localhost:5000/get_policy?table=${table}`);
      const fetchedData = response.data.data;

      // Mapping the array-based response to an object with column headers
      const formattedData = fetchedData.map(row => {
        let formattedRow = {};
        if (table === "blocked_urls") {
          formattedRow.url = row[0];
          formattedRow.type = row[1];
        } else if (table === "blocked_files") {
          formattedRow.file_hash = row[0];
          formattedRow.file_name = row[1];
        } else if (table === "blocked_mimetypes") {
          formattedRow.mime_type = row[0];
        } else if (table === "redirect_urls") {
          formattedRow.source_url = row[0];
          formattedRow.destination_url = row[1];
          formattedRow.proxy = row[2];
        } else if (table === "tls_excluded_hosts") {
          formattedRow.hostname = row[0];
        }
        return formattedRow;
      });

      setData(formattedData);

      // Dynamically set columns (headers) based on the formatted data
      if (formattedData.length > 0) {
        setColumns(Object.keys(formattedData[0]));
        setFilters(Object.fromEntries(Object.keys(formattedData[0]).map(key => [key, ""])));
      }

    } catch (err) {
      setError("Error fetching data from the server");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // Fetch data when the component mounts or the table changes
  }, [table]);

  // Helper function to get unique values for filter dropdown
  const getUniqueValues = (key) => {
    let values = [];
    data.forEach(item => {
      const value = item[key];
      if (value !== null && value !== undefined && !values.includes(value)) {
        values.push(value);
      }
    });
    return values.sort((a, b) => a.toString().localeCompare(b.toString()));
  };

  // Handle filter changes
  const handleFilterChange = (e, column) => {
    setFilters({ ...filters, [column]: e.target.value });
  };

  // Apply filters to the data
  const filteredData = data.filter(item =>
    Object.keys(filters).every(key => {
      const filterValue = filters[key].toLowerCase();
      const itemValue = item[key];
      if (filterValue === "") return true; // If no filter, show all
      return itemValue.toString().toLowerCase().includes(filterValue);
    })
  );

  // Format the cell value for display
  const formatCell = (value) => {
    if (value === null || value === undefined) return "N/A"; // Default value if the cell is null or undefined
    return value;
  };

  // Clear all filters
  const clearFilters = () => {
    const resetFilters = Object.fromEntries(Object.keys(filters).map(key => [key, ""]));
    setFilters(resetFilters);
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Policy Items</h1>

      {/* Clear Filters Button */}
      <div className="mb-4">
        <button
          onClick={clearFilters}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Clear Filters
        </button>
      </div>

      {/* Dropdown to select the table */}
      <select
        value={table}
        onChange={(e) => setTable(e.target.value)}
        className="mb-4 p-2 border"
      >
        {tableOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* Show loading indicator */}
      {loading && <p>Loading...</p>}

      {/* Show error message */}
      {error && <p>{error}</p>}

      {/* Display data in a table */}
      {data.length === 0 ? (
        <p>No data available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                {/* Headers */}
                {columns.map((key, index) => (
                  <th key={index} className="border p-2">
                    {key.replace("_", " ").toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Filter Row */}
              <tr className="bg-gray-100">
                {columns.map((key, index) => (
                  <td key={index} className="border p-2">
                    <select
                      value={filters[key] || ""}
                      onChange={(e) => handleFilterChange(e, key)}
                      className="p-1 w-full text-sm border rounded"
                    >
                      <option value="">-- Filter {key.replace("_", " ")} --</option>
                      {getUniqueValues(key).map((value, idx) => {
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

              {/* Data Rows */}
              {filteredData.map((item, index) => (
                <tr key={index} className="border">
                  {columns.map((key, idx) => (
                    <td key={idx} className="border p-2">
                      {formatCell(item[key])}
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
};

export default Policy;

import React, { useState, useEffect } from "react";
import axios from "axios";

const Policy = () => {
  const [table, setTable] = useState("blocked_urls");
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
    fetchData();
  }, [table]);

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

  const handleFilterChange = (e, column) => {
    setFilters({ ...filters, [column]: e.target.value });
  };

  const filteredData = data.filter(item =>
    Object.keys(filters).every(key => {
      const filterValue = filters[key].toLowerCase();
      const itemValue = item[key];
      if (filterValue === "") return true;
      return itemValue.toString().toLowerCase().includes(filterValue);
    })
  );

  const formatCell = (value) => {
    if (value === null || value === undefined) return "N/A";
    return value;
  };

  const clearFilters = () => {
    const resetFilters = Object.fromEntries(Object.keys(filters).map(key => [key, ""]));
    setFilters(resetFilters);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-extrabold text-gray-800 mb-6">Policy Items</h1>

      {/* Clear Filters Button */}
      <div className="mb-4">
        <button
          onClick={clearFilters}
          className="px-5 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-lg shadow-md hover:scale-105 transition"
        >
          Clear Filters
        </button>
      </div>

      {/* Dropdown to select the table */}
      <select
        value={table}
        onChange={(e) => setTable(e.target.value)}
        className="mb-4 p-3 border border-gray-300 rounded-lg shadow-sm text-gray-700 focus:ring-2 focus:ring-blue-400 focus:outline-none"
      >
        {tableOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* Show loading indicator */}
      {loading && <p className="text-gray-500">Loading...</p>}

      {/* Show error message */}
      {error && <p className="text-red-500">{error}</p>}

      {/* Display data in a table */}
      {data.length === 0 ? (
        <p className="text-gray-500">No data available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse rounded-lg shadow-md bg-white">
            <thead>
              <tr className="bg-gray-700 text-white">
                {columns.map((key, index) => (
                  <th key={index} className="border p-3 text-left">
                    {key.replace("_", " ").toUpperCase()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="bg-gray-100">
                {columns.map((key, index) => (
                  <td key={index} className="border p-2">
                    <select
                      value={filters[key] || ""}
                      onChange={(e) => handleFilterChange(e, key)}
                      className="p-2 w-full text-sm border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-400"
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

              {filteredData.map((item, index) => (
                <tr key={index} className="border bg-white hover:bg-gray-100 transition">
                  {columns.map((key, idx) => (
                    <td key={idx} className="border p-3 text-gray-700">
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

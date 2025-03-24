import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth0 } from "@auth0/auth0-react";
import { jwtDecode } from "jwt-decode";

function Logs() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0(); // Get Auth0 token
  const [logs, setLogs] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false); // Loading state

  useEffect(() => {
    if (isAuthenticated) {
      // Function to fetch logs from the API
      const fetchLogs = async () => {
        setLoading(true); // Set loading to true when fetching data
        try {
          // Get the token from Auth0
          const token = await getAccessTokenSilently();
          console.log("Token:", token);  // Debugging the token

          if (!token) {
            setError("No token available");
            return;
          }
          console.log("Token structure:", token.split('.')); // Split the token into parts
          // Decode the JWT and check the kid
    //      const decodedToken = jwtDecode(token);
    //      console.log("Decoded Token:", decodedToken);
    //      console.log("Kid from Token:", decodedToken.kid);

          // Send the token with the request
          const response = await axios.get("http://localhost:5000/logs", {
            headers: {
            'Authorization': `Bearer ${token}`, // Attach token here
            },
          });

          console.log("Request headers:", response.config.headers); // Debugging the request headers

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
    if (typeof value === "string" || typeof value === "number") {
      return value.toString().toLowerCase().includes(filterValue.toLowerCase());
    }
    if (typeof value === "object" && value !== null) {
      for (let key in value) {
        if (checkIfValueMatchesFilter(value[key], filterValue)) {
          return true;
        }
      }
    }
    return false;
  };

  const getUniqueValues = (key, logsToFilter) => {
    let values = [];
    logsToFilter.forEach(log => {
      const value = log[key];
      if (value === null || value === undefined) return;
      if (typeof value === "object" && value !== null) {
        Object.entries(value).forEach(([subKey, subValue]) => {
          if (typeof subValue === "string" || typeof subValue === "number") {
            values.push(subValue);
          }
        });
      } else {
        values.push(value);
      }
    });
    return [...new Set(values)].filter(value => value !== "").sort((a, b) => a.toString().localeCompare(b.toString()));
  };

  const handleFilterChange = (e, column) => {
    setFilters({ ...filters, [column]: e.target.value });
  };

  const filteredLogs = logs.filter(log =>
    Object.keys(filters).every(key => {
      const filterValue = filters[key].toLowerCase();
      const logValue = log[key];
      if (filterValue === "") return true;
      return checkIfValueMatchesFilter(logValue, filterValue);
    })
  );

  const formatCell = (value) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "object" && value !== null) {
      return Object.entries(value).map(([subKey, subValue]) => {
        if (typeof subValue === "object") {
          return <div key={subKey}>{subKey}: [object]</div>;
        }
        return (
          <div key={subKey}>
            <strong>{subKey}:</strong> {subValue}
          </div>
        );
      });
    }
    return value;
  };

  const clearFilters = () => {
    const resetFilters = Object.fromEntries(Object.keys(filters).map(key => [key, ""]));
    setFilters(resetFilters);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Logs</h2>

      {/* Loading Spinner */}
      {loading && <p className="text-gray-500 mt-4">Loading...</p>}

      {/* Error Message */}
      {error && <p className="text-red-500">{error}</p>}

      <button
        onClick={clearFilters}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Clear Filters
      </button>

      {logs.length === 0 && !loading ? (
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

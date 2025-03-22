import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";

function Logs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:5000/logs")
      .then(response => {
        console.log("API Response:", response.data); // Debugging
        const extractedLogs = response.data?.logs?.logs || []; // Correct extraction
        setLogs(Array.isArray(extractedLogs) ? extractedLogs : []);
      })
      .catch(error => console.error("Error fetching logs:", error));
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Logs</h2>
      {logs.length === 0 ? (
        <p className="text-gray-500 mt-4">No logs available.</p>
      ) : (
        <ul className="mt-4">
          {logs.map((log, index) => (
            <li key={index} className="border p-2 my-2 rounded">
              <p><strong>Method:</strong> {log.method}</p>
              <p><strong>Category:</strong> {log.category}</p>
              <p><strong>Status:</strong> {log.status_code}</p>
              <p><strong>Response Time:</strong> {log.response_time?.toFixed(2)}s</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function BlockList() {
  const [list, setList] = useState([]);
  const [newItem, setNewItem] = useState("");

  useEffect(() => {
    axios.get("http://localhost:5000/blocklist")
      .then(response => {
        console.log("Blocklist API Response:", response.data); // Debugging
        setList(Array.isArray(response.data.blocklist) ? response.data.blocklist : []);
      })
      .catch(error => console.error("Error fetching block list:", error));
  }, []);

  const addItem = () => {
    if (!newItem.trim()) return; // Prevent empty submissions

    axios.post("http://localhost:5000/blocklist", { value: newItem })
      .then(() => {
        setList([...list, newItem]);
        setNewItem("");
      })
      .catch(error => console.error("Error adding item:", error));
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Block List</h2>
      <ul className="mt-4">
        {list.map((item, index) => (
          <li key={index} className="border p-2 my-2 rounded">{item}</li>
        ))}
      </ul>
      <div className="mt-4">
        <input
          type="text"
          value={newItem}
          onChange={e => setNewItem(e.target.value)}
          className="border p-2"
          placeholder="Add to block list"
        />
        <button
          onClick={addItem}
          className="bg-blue-500 text-white p-2 ml-2 rounded"
        >
          Add
        </button>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <nav className="p-4 bg-gray-800 text-white flex space-x-4">
        <Link to="/" className="hover:underline">Logs</Link>
        <Link to="/blocklist" className="hover:underline">Block List</Link>
      </nav>
      <div className="max-w-3xl mx-auto">
        <Routes>
          <Route path="/" element={<Logs />} />
          <Route path="/blocklist" element={<BlockList />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

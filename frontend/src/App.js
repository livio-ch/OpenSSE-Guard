import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Logs from "./Logs"; // Import the Logs component
import BlockList from "./BlockList"; // You can add this file later for the blocklist page

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

  import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
  import Logs from "./Logs";
  import Policy from "./Policy";
  import './App.css'; // Import your CSS file here

  function App() {
    return (
      <Router>
        <nav className="p-4 bg-gray-900 text-white flex justify-center gap-6 shadow-lg">
          <Link to="/" className="hover:text-blue-400 transition">Logs</Link>
          <Link to="/policy" className="hover:text-blue-400 transition">Policy</Link>
        </nav>
        <div className="max-w-5xl mx-auto p-6">
          <Routes>
            <Route path="/" element={<Logs />} />
            <Route path="/policy" element={<Policy />} />
          </Routes>
        </div>
      </Router>
    );
  }

  export default App;

import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useState } from "react";
import Logs from "./Logs";
import Logs2 from "./Logs2";

import Policy from "./Policy";
import "./App.css"; // Import your CSS file here

function App() {
  const { loginWithRedirect, logout, user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();
  const [apiResponse, setApiResponse] = useState("");

  if (isLoading) {
    return <div>Loading...</div>;
  }

  // Function to call Flask API with Auth0 token
  const fetchProtectedData = async () => {
    try {
      const token = await getAccessTokenSilently(); // Fetch Auth0 token

      const response = await fetch("http://127.0.0.1:5000/protected", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`, // Attach token
        },
      });

      const data = await response.json();
      setApiResponse(data);
    } catch (error) {
      console.error("Error fetching API:", error);
      setApiResponse({ error: "Failed to fetch API" });
    }
  };

  return (
    <Router>
      <nav className="p-4 bg-gray-900 text-white flex justify-between items-center shadow-lg">
        <div className="flex gap-6">
          {isAuthenticated ? (
            <>
              <Link to="/" className="text-lg hover:text-blue-400 transition">Logs</Link>
              <Link to="/logs2" className="text-lg hover:text-blue-400 transition">Logs2</Link>
              <Link to="/policy" className="text-lg hover:text-blue-400 transition">Policy</Link>
            </>
          ) : null}
        </div>

        {/* This div will grow to fill the available space and push login/logout to the far right */}
        <div className="flex-grow"></div>

        <div>
          {!isAuthenticated ? (
            <a
              href="#"
              onClick={() => loginWithRedirect()}
              className="text-lg hover:text-blue-400 transition cursor-pointer"
            >
              Log in
            </a>
          ) : (
            <a
              href="#"
              onClick={() => logout({ returnTo: window.location.origin })}
              className="text-lg hover:text-blue-400 transition cursor-pointer"
            >
              Log out
            </a>
          )}
        </div>
      </nav>

      <div className="max-w-5xl mx-auto p-6">
        <Routes>
          {isAuthenticated && (
            <>
              <Route path="/" element={<Logs />} />
              <Route path="/logs2" element={<Logs2 />} />
              <Route path="/policy" element={<Policy />} />
            </>
          )}
        </Routes>
      </div>

      {/* Show API response */}
      {apiResponse && <pre>{JSON.stringify(apiResponse, null, 2)}</pre>}
    </Router>
  );
}

export default App;

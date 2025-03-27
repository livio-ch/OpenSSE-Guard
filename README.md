# OpenSSE-Guard 🛡️

**An open-source Security Service Edge (SSE) proxy for filtering, monitoring, and redirecting HTTP traffic using mitmproxy, Flask, and a React-based admin interface.**

---

## ⚠️ Disclaimer  

🚧 **This is a playground project and should not be used in production.**  
OpenSSE-Guard was heavily developed with the support of AI (such as ChatGPT) and is still in an experimental stage. Expect incomplete features, potential security issues, and breaking changes. Use at your own risk.  

---

## 🚀 Overview

OpenSSE-Guard is a lightweight security tool that intercepts HTTP(S) traffic, analyzes URLs, and applies security policies such as:

- **Blocking malicious or unwanted domains**
- **Redirecting traffic based on security rules**
- **Forwarding requests to a different proxy when needed**

Built with **mitmproxy** and **Flask**, OpenSSE-Guard acts as a dynamic security gateway—ideal for enterprise security, content filtering, and web traffic control.  
**Authentication is handled using Auth0 for secure access control.**

---

## 🔹 Features

- **Custom URL Filtering:** Block or redirect requests based on domains, hostnames, or URL patterns.
- **Dynamic Proxy Forwarding:** Reroute requests to another proxy when necessary.
- **Policy CRUD Operations:** Create, read, update (if implemented), and delete policy entries via a RESTful API.
- **React Admin Interface:** Manage policies through a dynamic web interface with filtering, sorting, and add/delete functionality.
- **Authentication with Auth0:** Secure user authentication and role-based access control.
- **Security-First Design:** Helps enforce **SSE (Security Service Edge)** policies.
- **Stream Handling & Content Analysis:** Intercepts and processes HTTP responses with content-based rules.
- **Threat Intelligence Integration:** Validate URLs and file hashes against the AlienVault OTX API.

---

## 🔹 Installation

### Prerequisites

Ensure you have the following installed:
- **Python 3.7+**
- **mitmproxy** (for traffic interception)
- **Flask** (for the API layer)
- **Node.js & npm** (if using the React admin interface)

### Setup

1. **Clone the repository:**

   ```sh
   git clone https://github.com/livio-ch/OpenSSE-Guard.git
   cd OpenSSE-Guard
   ```

2. **Install Backend Dependencies:**

   (Optionally create and activate a virtual environment first.)

   ```sh
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies** (if using the React admin interface):

   ```sh
   cd frontend
   npm install
   ```

---

## 🔹 Configuration

### Environment Variables

Create a `.env` file in your project root (or backend directory) with content similar to:

```dotenv
OTX_API_KEY=your_otx_api_key_here
DB_PATH=url_filter.db
AUTH0_DOMAIN=your_auth0_domain
AUTH0_AUDIENCE=your_auth0_audience
```

*Tip:* Ensure your `.env` is listed in `.gitignore` to avoid committing sensitive data.

### CORS

The Flask backend is configured to allow requests from `http://localhost:3000`. Adjust this in the Flask code if necessary.

---

## 🔹 Running the Application

### Running the Backend (Flask API)

Start the Flask API:

```sh
python app.py
```

This will run the server on `http://0.0.0.0:5000` (or `http://localhost:5000`) in debug mode. The API provides endpoints for managing policies, checking URLs, file hashes, and more.

### Running mitmproxy

Run mitmproxy with your interception script:

```sh
mitmproxy -s api_call_intercept.py
```

Configure your network/browser proxy to `http://127.0.0.1:8080`.

### Running the Frontend (React Admin Interface)

If you choose to use the provided React admin interface for managing policies:

1. Navigate to the `frontend` directory:

   ```sh
   cd frontend
   ```

2. Start the React app:

   ```sh
   npm start
   ```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the policy management interface.

---

## 🔹 How It Works

1. **Traffic Interception:**  
   mitmproxy intercepts HTTP(S) traffic.

2. **Policy Evaluation:**  
   The intercepted requests are forwarded to the Flask API, which checks URLs against allowlists, blocklists, and threat intelligence (via OTX).

3. **Authentication & Authorization:**  
   Access to the API and admin interface is secured with Auth0, ensuring only authorized users can manage policies.

4. **Policy Actions:**  
   Based on security rules, the proxy will block, allow, or redirect traffic.

5. **Policy Management:**  
   Use the API endpoints (or React admin interface) to manage policies:
   - Add new policies
   - Retrieve existing policies
   - Delete policies
   - (Optionally) Update policies

---

## 🔹 API Endpoints

### GET `/get_policy`
Retrieve policy data from a specified table.

- **Query Parameter:**  
  `table` (e.g., `blocked_urls`)
- **Response Example:**
  ```json
  {
    "status": "success",
    "data": [
      ["www.google.com", "domain"],
      ["example.com", "hostname"]
    ]
  }
  ```

### POST `/set_policy`
Add a new policy entry.

- **Expected JSON Payload:**
  ```json
  {
    "table": "blocked_urls",
    "data": { "url": "www.google.com", "type": "domain" }
  }
  ```
*Note:* The backend maps the JSON keys to the appropriate database columns.

### DELETE `/delete_policy`
Delete a policy entry.

- **Expected JSON Payload:**
  ```json
  {
    "table": "blocked_urls",
    "condition": "www.google.com"
  }
  ```
If the condition string does not specify a column, the backend assumes the first column (e.g., `value` for `blocked_urls`).

### Additional Endpoints

- **POST `/checkUrl`** – Validate a URL against policies and OTX.
- **POST `/checkHash`** – Check a file hash against policies and OTX.
- **POST `/checkMimeType`** – Validate a MIME type.
- **GET `/logs`** – Retrieve log entries.
- *(Optional)* **PUT `/update_policy`** – Update an existing policy entry.

---

## 🔹 Deployment

### Frontend Deployment

Build the React app for production:

```sh
npm run build
```

This creates a production-ready bundle in the `/build` folder.

### Backend Deployment

For production, consider using a production WSGI server (e.g., Gunicorn) with a reverse proxy (e.g., Nginx). Adjust your CORS, logging, and error handling settings accordingly.

---

## 🔹 Contributing

Contributions are welcome! Please submit issues, feature requests, or pull requests on GitHub.

---

## 🔹 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 🔹 Contact

For questions or discussions, please use GitHub Issues or open a discussion.

---

🚀 **Secure your web traffic with OpenSSE-Guard today!**

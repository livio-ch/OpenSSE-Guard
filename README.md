# OpenSSE-Guard 🛡️

**An open-source Security Service Edge (SSE) proxy for filtering, monitoring, and redirecting HTTP traffic using mitmproxy and Flask.**

## 🚀 Overview
OpenSSE-Guard is a lightweight security tool that intercepts HTTP(S) traffic, analyzes URLs, and applies security policies such as:

✅ **Blocking malicious or unwanted domains**  
✅ **Redirecting traffic based on security rules**  
✅ **Forwarding requests to a different proxy when needed**  

Built with **mitmproxy** and **Flask**, OpenSSE-Guard acts as a dynamic security gateway, making it ideal for **enterprise security, content filtering, and web traffic control**.

## 🔹 Features
- **Custom URL Filtering** – Block or redirect requests based on domains, hostnames, or URL patterns.
- **Dynamic Proxy Forwarding** – Reroute requests to another proxy when necessary.
- **Security-First Design** – Helps enforce **SSE (Security Service Edge)** policies.
- **Lightweight & Extensible** – Easily integrates with other security tools.

## 🔹 Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.7+
- mitmproxy
- Flask

### Setup
```sh
# Clone the repository
git clone https://github.com/livio-ch/OpenSSE-Guard.git
cd OpenSSE-Guard

# Install dependencies
pip install -r requirements.txt
```

## 🔹 Usage
### 1️⃣ **Start the Flask API**
```sh
python app.py
```

### 2️⃣ **Run mitmproxy with the script**
```sh
mitmproxy -s api_call_intercept.py
```

### 3️⃣ **Configure your network to use mitmproxy** (for interception)
- Set your browser/system proxy to `http://127.0.0.1:8080`

## 🔹 How It Works
1. **Intercepts HTTP requests** via mitmproxy.
2. **Checks URLs** against allowlists and blocklists via the Flask API.
3. **Applies security rules** (block, allow, or forward requests to another proxy).
4. **Forwards traffic** accordingly.

## 🔹 Contributing
Contributions are welcome! Feel free to submit issues, feature requests, or pull requests.

## 🔹 License
MIT License. See `LICENSE` for details.

## 🔹 Contact
Have questions? Reach out via GitHub Issues or open a discussion!

---
🚀 **Secure your web traffic with OpenSSE-Guard today!**

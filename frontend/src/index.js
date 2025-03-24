import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { Auth0Provider } from '@auth0/auth0-react';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));

const domain = "dev-qq26bf68b4ogkwa7.us.auth0.com"; // Replace with your Auth0 domain
const clientId = "EdV4hVycMAVhuEqQeS07DpP7xKrJKrVt"; // Replace with your Auth0 client ID

root.render(
  <Auth0Provider
    domain={domain}
    clientId={clientId}
    authorizationParams={{
      redirect_uri: window.location.origin,
      audience: "http://localhost:5000",
      scope: "all"
    }}
  >
    <React.StrictMode>
      <App />
    </React.StrictMode>
  </Auth0Provider>
);

reportWebVitals();

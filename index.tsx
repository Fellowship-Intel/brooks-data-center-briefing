console.log("Index.tsx IS RUNNING - Minimal Test");
import React from 'react';
import ReactDOM from 'react-dom/client';
// import App from './App';
// import { ErrorBoundary } from './components/ErrorBoundary';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <div style={{ color: 'white', padding: 20 }}>
      <h1>Minimal Test Works</h1>
    </div>
  </React.StrictMode>
);
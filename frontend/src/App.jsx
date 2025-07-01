import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Dashboard from './components/Dashboard';
import { WebSocketProvider } from './contexts/WebSocketContext';

function App() {
  return (
    <WebSocketProvider>
      <div className="min-h-screen bg-gray-100">
        <Toaster position="top-right" />
        <Dashboard />
      </div>
    </WebSocketProvider>
  );
}

export default App;
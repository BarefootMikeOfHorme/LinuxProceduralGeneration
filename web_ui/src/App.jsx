import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import NodeEditorPage from './pages/NodeEditorPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="studio" element={<NodeEditorPage />} />
          <Route path="monitoring" element={<div className="p-8 text-text-dim">Monitoring Module Loading...</div>} />
          <Route path="terminal" element={<div className="p-8 text-text-dim">Web Terminal Connecting...</div>} />
          <Route path="settings" element={<div className="p-8 text-text-dim">Settings Panel</div>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

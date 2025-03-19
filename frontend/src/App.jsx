import React, { useState, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';


function App() {

  return (
    <Router>
      <div className="app-container">
        <header className="app-header">
          <h1>PDF Assistant</h1>
          <p>Upload a PDF and ask questions about its content</p>
        </header>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App

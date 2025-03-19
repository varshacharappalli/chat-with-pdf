import React, { useState, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';

const ChatPage=()=>{
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [responses, setResponses] = useState([]);
    const messagesEndRef = useRef(null);
  
    const handleQueryChange = (e) => {
      setQuery(e.target.value);
    };
  
    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!query.trim()) return;
  
      const userQuery = query.trim();
      setResponses(prev => [...prev, { role: 'user', content: userQuery }]);
      setQuery('');
      setLoading(true);
  
      try {
        const response = await axios.get(`http://localhost:8000/chat/`, {
          params: { query: userQuery }
        });
  
        const responseData = {
          role: 'assistant',
          content: response.data.response,
          sources: response.data.sources
        };
  
        setResponses(prev => [...prev, responseData]);
        setLoading(false);
      } catch (err) {
        console.error('Error getting response:', err);
        setResponses(prev => [...prev, { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error processing your question. Please try again.',
          error: true
        }]);
        setLoading(false);
      }
    };
  
    React.useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [responses]);
  
    return (
      <div className="chat-container">
        <div className="chat-header">
          <h2>Ask questions about your PDF</h2>
          <a href="/" className="upload-new-link">Upload a new PDF</a>
        </div>
  
        <div className="messages-container">
          {responses.length === 0 ? (
            <div className="empty-chat">
              <svg className="chat-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"></path>
              </svg>
              <p>Ask a question about your PDF content</p>
            </div>
          ) : (
            responses.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                  {msg.sources && (
                    <div className="sources">
                      <h4>Sources:</h4>
                      <ul>
                        {msg.sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
  
        <form className="query-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            placeholder="Ask a question about your PDF..."
            disabled={loading}
            className="query-input"
          />
          <button 
            type="submit" 
            disabled={loading || !query.trim()} 
            className="submit-button"
          >
            {loading ? (
              <span className="loading-spinner"></span>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            )}
          </button>
        </form>
      </div>
    );
  }

  export default ChatPage;
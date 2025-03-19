import React, { useState, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';

const HomePage=()=>{const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError('');
    } else {
      setFile(null);
      setFileName('');
      setError('Please select a valid PDF file');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setFileName(droppedFile.name);
      setError('');
    } else {
      setError('Please drop a valid PDF file');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a PDF file to upload');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadResult(response.data);
      setLoading(false);
    } catch (err) {
      setError('Error uploading the file. Please try again.');
      setLoading(false);
      console.error('Upload error:', err);
    }
  };

  return (
    <div className="home-container">
      <div 
        className="upload-area"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <input 
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          className="file-input"
        />
        
        {!file ? (
          <div className="upload-placeholder">
            <svg className="upload-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            <p>Drag & drop your PDF file here or click to browse</p>
          </div>
        ) : (
          <div className="file-selected">
            <svg className="pdf-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <path d="M9 15h6M9 11h6"></path>
            </svg>
            <p>{fileName}</p>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
      
      <button 
        className={`upload-button ${loading ? 'loading' : ''}`} 
        onClick={handleUpload}
        disabled={!file || loading}
      >
        {loading ? 'Processing...' : 'Upload & Process PDF'}
      </button>

      {uploadResult && (
        <div className="upload-result">
          <h3>PDF Processed Successfully!</h3>
          <p>Pages processed: {uploadResult.pages_processed}</p>
          <p>Chunks processed: {uploadResult.chunks_processed}</p>
          <a href="/chat" className="start-chat-button">Start Asking Questions</a>
        </div>
      )}
    </div>
  );
}

export default HomePage;
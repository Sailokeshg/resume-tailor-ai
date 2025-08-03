import React, { useState, useRef } from 'react';

const FileUpload = ({ onFileSelect, loading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    setError('');
    
    // Validate file type
    if (!file.name.endsWith('.tex')) {
      setError('Please upload a .tex file only');
      return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }
    
    setFileName(file.name);
    onFileSelect(file);
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <label className="block text-base font-semibold text-gray-700 mb-2 tracking-wide">
        Upload Resume (.tex only)
      </label>
      
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 ${
          dragActive 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-300'
        } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!loading ? openFileDialog : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".tex"
          onChange={handleFileInput}
          className="hidden"
          disabled={loading}
        />
        
        <div className="flex flex-col items-center gap-3">
          <svg
            className={`w-12 h-12 ${dragActive ? 'text-blue-500' : 'text-gray-400'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {fileName ? fileName : 'Drop your .tex file here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {fileName ? 'File selected successfully' : 'or click to browse'}
            </p>
          </div>
          
          {!fileName && (
            <button
              type="button"
              className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              onClick={openFileDialog}
            >
              Choose File
            </button>
          )}
        </div>
      </div>
      
      {error && (
        <div className="mt-2 text-red-600 text-sm font-medium">
          {error}
        </div>
      )}
      
      {fileName && !error && (
        <div className="mt-2 text-green-600 text-sm font-medium">
          ✓ {fileName} ready for processing
        </div>
      )}
    </div>
  );
};

export default FileUpload;

import React, { useState, useRef } from "react";

const FileUpload = ({ onFileSelect, loading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
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
    setError("");

    // Validate file type
    if (!file.name.endsWith(".tex")) {
      setError("Please upload a .tex file only");
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
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
      <label className="label mb-2 block">Upload Resume (.tex only)</label>

      {!fileName ? (
        <div
          className={`dropzone ${dragActive ? "drag" : ""} ${loading ? "disabled" : ""}`}
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

          <div className="dropzone-content">
            <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div>
              <p className="dropzone-title">Drop your .tex file here</p>
              <p className="dropzone-sub">or click to browse</p>
            </div>
            <button type="button" className="btn btn-secondary" onClick={openFileDialog}>
              Choose File
            </button>
          </div>
        </div>
      ) : (
        <div className="file-meta">
          <div className="meta-left">
            <svg className="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="meta-text">
              <div className="meta-name" title={fileName}>{fileName}</div>
              <div className="meta-sub">Resume file ready for processing</div>
            </div>
          </div>
          <div className="meta-actions">
            <button type="button" onClick={openFileDialog} disabled={loading} className="btn btn-secondary">Change File</button>
            <input ref={fileInputRef} type="file" accept=".tex" onChange={handleFileInput} className="hidden" disabled={loading} />
          </div>
        </div>
      )}

      {error && <div className="toast toast-error mt-2">{error}</div>}
    </div>
  );
};

export default FileUpload;

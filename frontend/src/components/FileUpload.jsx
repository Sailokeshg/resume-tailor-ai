import React from "react";

const FileUpload = ({ onFileChange }) => (
  <div>
    <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={onFileChange} />
  </div>
);

export default FileUpload;

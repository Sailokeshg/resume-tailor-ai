import React from "react";

const ResumeViewer = ({ resume }) => (
  <div className="resume-viewer">
    <h3>Your Resume</h3>
    <pre>{resume}</pre>
  </div>
);

export default ResumeViewer;

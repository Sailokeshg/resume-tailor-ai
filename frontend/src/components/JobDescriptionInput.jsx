import React from "react";

const JobDescriptionInput = ({ value, onChange }) => (
  <div>
    <label>Job Description:</label>
    <textarea value={value} onChange={onChange} rows={6} />
  </div>
);

export default JobDescriptionInput;

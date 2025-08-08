import React from "react";

const JobDescriptionInput = ({ value, onChange, disabled }) => (
  <div>
    <label className="block text-base font-semibold text-gray-700 mb-2 tracking-wide">
      Job Description
    </label>
    <textarea
      className="editor-textarea"
      value={value}
      onChange={onChange}
      rows={6}
      disabled={disabled}
      placeholder="Paste the job description here..."
    />
  </div>
);

export default JobDescriptionInput;

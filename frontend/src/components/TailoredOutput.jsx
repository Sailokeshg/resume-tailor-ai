import React from "react";

const TailoredOutput = ({ output }) => (
  <div className="tailored-output">
    <h3>Tailored Resume</h3>
    <textarea value={output} readOnly rows={10} />
  </div>
);

export default TailoredOutput;

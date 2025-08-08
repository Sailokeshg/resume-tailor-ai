import React, { useRef } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

const TailoredOutput = ({ output }) => {
  const codeRef = useRef(null);

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-2xl font-semibold">Tailored Resume</h2>
       
      </div>
      <div className="w-full h-96 overflow-auto border-2 border-blue-400 rounded-lg bg-white text-black">
        <div ref={codeRef}>
          <SyntaxHighlighter
            language="latex"
            style={oneLight}
            customStyle={{
              background: "transparent",
              fontSize: "1rem",
              minHeight: "100%",
              margin: 0,
              padding: "1rem",
              fontFamily: "Fira Mono, Menlo, Monaco, 'Courier New', monospace",
            }}
            showLineNumbers
          >
            {output || "% No output yet"}
          </SyntaxHighlighter>
        </div>
      </div>
    </div>
  );
};

export default TailoredOutput;

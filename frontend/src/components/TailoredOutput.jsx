import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

const TailoredOutput = ({ output }) => {
  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold mb-2">Tailored Resume</h2>
      <div className="w-full h-96 overflow-auto border-2 border-blue-400 rounded-lg bg-white text-black">
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
  );
};

export default TailoredOutput;

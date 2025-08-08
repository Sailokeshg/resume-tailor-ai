import React, { useEffect, useRef, useState } from "react";
import Editor from "react-simple-code-editor";
import Prism from "prismjs";
import "prismjs/components/prism-latex";

const TailoredOutput = ({ output }) => {
  const codeRef = useRef(null);
  const [text, setText] = useState(output || "");

  useEffect(() => {
    setText(output || "");
  }, [output]);

  const highlight = (code) => {
    const language = Prism.languages.latex || Prism.languages.markup;
    return Prism.highlight(code, language, "latex");
  };

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-2xl font-semibold">Tailored Resume</h2>
      </div>
      <div className="w-full border border-gray-200 rounded-xl bg-white text-black shadow-sm">
        <div ref={codeRef}>
          <Editor
            value={text}
            onValueChange={setText}
            highlight={highlight}
            padding={16}
            textareaId="tailored-resume-editor"
            className="outline-none language-latex"
            style={{
              fontFamily: "Fira Mono, Menlo, Monaco, 'Courier New', monospace",
              fontSize: 14.5,
              minHeight: "24rem",
              overflow: "auto",
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default TailoredOutput;

import React, { useEffect, useMemo, useRef, useState } from "react";
import Editor from "react-simple-code-editor";
import Prism from "prismjs";
import "prismjs/components/prism-latex";
import { Document, Page, pdfjs } from "react-pdf";
import api from "../services/api";

// Configure the PDF.js worker to the exact API version that react-pdf is using
// This avoids version mismatches between the core library and the worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const TailoredOutput = ({ output }) => {
  const codeRef = useRef(null);
  const [text, setText] = useState(output || "");
  const [pdfBlobUrl, setPdfBlobUrl] = useState("");
  const [compileError, setCompileError] = useState("");
  const [numPages, setNumPages] = useState(null);

  useEffect(() => {
    setText(output || "");
  }, [output]);

  // Debounced PDF compilation whenever text changes
  useEffect(() => {
    if (!text) {
      setPdfBlobUrl("");
      setCompileError("");
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setCompileError("");
        const blob = await api.compilePdf(text);
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
      } catch (e) {
        setCompileError(e.message || "Compilation failed");
        setPdfBlobUrl("");
      }
    }, 600);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [text]);

  const highlight = (code) => {
    const language = Prism.languages.latex || Prism.languages.markup;
    return Prism.highlight(code, language, "latex");
  };

  return (
    <div className="mt-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-2xl font-semibold">Tailored LaTeX</h2>
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
                  minHeight: "28rem",
                  overflow: "auto",
                }}
              />
            </div>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-2xl font-semibold">Live PDF Preview</h2>
            {pdfBlobUrl && (
              <a
                href={pdfBlobUrl}
                download="tailored-resume.pdf"
                className="text-sm px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
              >
                Download
              </a>
            )}
          </div>
          <div className="w-full border border-gray-200 rounded-xl bg-white shadow-sm p-2 min-h-[28rem] flex items-center justify-center">
            {compileError ? (
              <div className="text-red-600 text-sm whitespace-pre-wrap">{compileError}</div>
            ) : pdfBlobUrl ? (
              <Document
                file={pdfBlobUrl}
                onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                onLoadError={(err) => setCompileError(err?.message || "Failed to load PDF file")}
              >
                <Page pageNumber={1} width={600} renderTextLayer={false} renderAnnotationLayer={false} />
              </Document>
            ) : (
              <p className="text-gray-500">PDF preview will appear here.</p>
            )}
          </div>
          {numPages && numPages > 1 && (
            <p className="text-xs text-gray-500 mt-1">Showing page 1 of {numPages}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TailoredOutput;

import React, { useEffect, useRef, useState } from "react";
import Editor from "react-simple-code-editor";
import Prism from "prismjs";
import "prismjs/components/prism-latex";
import { Document, Page, pdfjs } from "react-pdf";
import api from "../services/api";

// Configure the PDF.js worker to the exact API version that react-pdf is using
// This avoids version mismatches between the core library and the worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const TailoredOutput = ({ output, resumeContent, loading }) => {
  const codeRef = useRef(null);
  const [text, setText] = useState(output || "");
  const [pdfBlobUrl, setPdfBlobUrl] = useState("");
  const [compileError, setCompileError] = useState("");
  const [numPages, setNumPages] = useState(null);
  const previewRef = useRef(null);
  const [pageWidth, setPageWidth] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    // Decide what to show inside the code panel based on app state
    if (loading) {
      setText("");
      return;
    }
    if (output) {
      setText(output || "");
      return;
    }
    if (resumeContent) {
      setText(resumeContent || "");
      return;
    }
    setText("");
  }, [output, resumeContent, loading]);

  // Debounced PDF compilation whenever text changes
  useEffect(() => {
    if (!text) {
      setPdfBlobUrl("");
      setCompileError("");
      setNumPages(null);
      setCurrentPage(1);
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setCompileError("");
        setNumPages(null);
        setCurrentPage(1);
        const blob = await api.compilePdf(text);
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
      } catch (e) {
        setCompileError(e.message || "Compilation failed");
        setPdfBlobUrl("");
        setNumPages(null);
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

  // Fit PDF page to container width
  useEffect(() => {
    if (!previewRef.current) return;
    const element = previewRef.current;
    const update = () => {
      // subtract small padding
      const width = Math.floor(element.clientWidth - 16);
      setPageWidth(width > 0 ? width : 0);
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    window.addEventListener("orientationchange", update);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("orientationchange", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  // Derived UI state
  const mode = loading ? "loading" : output ? "output" : resumeContent ? "uploaded" : "empty";
  const panelTitle = mode === "uploaded" ? "Your resume" : "Tailored LaTeX";

  const goPrev = () => setCurrentPage((p) => Math.max(1, p - 1));
  const goNext = () => setCurrentPage((p) => (numPages ? Math.min(numPages, p + 1) : p + 1));

  return (
    <>
      {/* Editor Panel */}
      <section className="panel">
        <div className="panel-header"><h2>{panelTitle}</h2></div>
        <div className="panel-body panel-body-fill">
          {text ? (
            <div className="code-surface" ref={codeRef}>
              <Editor
                value={text}
                onValueChange={setText}
                highlight={highlight}
                padding={16}
                textareaId="tailored-resume-editor"
                className="outline-none language-latex code-editor"
                style={{
                  fontFamily: "Fira Mono, Menlo, Monaco, 'Courier New', monospace",
                  fontSize: 14.5,
                }}
              />
            </div>
          ) : (
            <div className="placeholder-surface">
              {mode === "loading" ? (
                <div className="notice">Tailored LaTeX will appear here…</div>
              ) : (
                <div className="notice">Your LaTeX will appear here.</div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Preview Panel */}
      <section className="panel">
        <div className="panel-header panel-header-actions">
          <h2>Live PDF Preview</h2>
          <div className="preview-actions">
            {pdfBlobUrl && numPages && numPages > 1 && (
              <div className="pager">
                <button className="btn btn-secondary" onClick={goPrev} disabled={currentPage <= 1}>Prev</button>
                <span className="pager-text">{currentPage} / {numPages}</span>
                <button className="btn btn-secondary" onClick={goNext} disabled={currentPage >= numPages}>Next</button>
              </div>
            )}
            {pdfBlobUrl && (
              <a href={pdfBlobUrl} download="tailored-resume.pdf" className="btn btn-secondary">Download</a>
            )}
          </div>
        </div>
        <div className="panel-body panel-body-fill preview-surface" ref={previewRef}>
          {compileError ? (
            <div className="notice error">{compileError}</div>
          ) : pdfBlobUrl ? (
            <Document
              file={pdfBlobUrl}
              onLoadSuccess={({ numPages }) => setNumPages(numPages)}
              onLoadError={(err) => setCompileError(err?.message || "Failed to load PDF file")}
            >
              <Page pageNumber={currentPage} width={pageWidth || 720} renderTextLayer={false} renderAnnotationLayer={false} />
            </Document>
          ) : (
            <div className="notice">PDF preview will appear here.</div>
          )}

          {pdfBlobUrl && numPages && numPages > 1 && (
            <div className="preview-meta">Showing page {currentPage} of {numPages}</div>
          )}
        </div>
      </section>
    </>
  );
};

export default TailoredOutput;

import React, { useState } from "react";
import FileUpload from "../components/FileUpload.jsx";
import TailoredOutput from "../components/TailoredOutput.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import useResumeTailor from "../hooks/useResumeTailor.js";
import DescriptionIcon from "@mui/icons-material/Description";

const ResumeTailorPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [resumeContent, setResumeContent] = useState("");
  const [jobDesc, setJobDesc] = useState("");
  const { output, suggestions, improvementsSummary, loading, error, tailorResume } =
    useResumeTailor();
  const [showInputs, setShowInputs] = useState(true);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (evt) => {
      setResumeContent(evt.target.result);
    };
    reader.readAsText(file);
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!resumeContent || !jobDesc) {
      return;
    }
    tailorResume(resumeContent, jobDesc);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-icon">
            <DescriptionIcon fontSize="small" />
          </span>
          <div className="brand-text">
            <span className="title">Resume Tailor AI</span>
            <span className="subtitle">Smart tailoring for LaTeX resumes</span>
          </div>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowInputs((v) => !v)}
          >
            {showInputs ? "Hide Inputs" : "Show Inputs"}
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !resumeContent || !jobDesc}
            className="btn btn-primary"
          >
            {loading ? (
              <span className="flex items-center gap-2"><LoadingSpinner /> Tailoring…</span>
            ) : (
              "Tailor Resume"
            )}
          </button>
        </div>
      </header>

      <main className={`app-main ${showInputs ? "" : "no-inputs"}`}>
        {/* Inputs Panel */}
        {showInputs && (
          <section className="panel">
            <div className="panel-header">
              <h2>Inputs</h2>
            </div>
            <div className="panel-body">
              <FileUpload onFileSelect={handleFileSelect} loading={loading} />
              <div className="space-y-2 mt-6">
                <label className="label">Job Description</label>
                <textarea
                  className="textarea"
                  placeholder="Paste the job description here…"
                  value={jobDesc}
                  onChange={(e) => setJobDesc(e.target.value)}
                  disabled={loading}
                  rows={12}
                />
              </div>

              {error && (
                <div className="toast toast-error mt-4">{error}</div>
              )}

              {improvementsSummary && (
                <div className="summary mt-6">
                  <div className="summary-header">Improvements Summary</div>
                  <div className="summary-body whitespace-pre-wrap">{improvementsSummary}</div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Editor + Preview Panels */}
        <TailoredOutput output={output} />
      </main>

      <footer className="app-footer">
        &copy; {new Date().getFullYear()} <span className="font-semibold">Resume Tailor AI</span>
      </footer>
    </div>
  );
};

export default ResumeTailorPage;

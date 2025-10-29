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
  const [model, setModel] = useState("DEEPSEEK_R1_0528");
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
    tailorResume(resumeContent, jobDesc, model);
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
          <select
            className="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={loading}
          >
            <option value="DEEPSEEK_R1_0528">DeepSeek: R1 0528</option>
            <option value="DEEPSEEK_V3_0324">DeepSeek: V3 0324</option>
            <option value="DEEPSEEK_R1T2">DeepSeek: R1T2</option>
            <option value="QWEN3_235B_A22B">Qwen3 235B A22B</option>
            <option value="Z.AI_GLM_4_5_AIR">Z.AI: GLM 4.5 Air</option>
            <option value="MICROSOFT_MAI_DS_R1">Microsoft: MAI DS R1</option>
            <option value="MOONSHOTAI_KIMI_VL_A3B_THINKING">Moonshot AI: Kimi VL A3B Thinking</option>
          </select>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowInputs((v) => !v)}
          >
            {showInputs ? "Hide Panel" : "Show Panel"}
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
        <TailoredOutput output={output} resumeContent={resumeContent} loading={loading} />
      </main>

      <footer className="app-footer">
        &copy; {new Date().getFullYear()} <span className="font-semibold">Resume Tailor AI</span>
      </footer>
    </div>
  );
};

export default ResumeTailorPage;

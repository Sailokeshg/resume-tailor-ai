import React, { useState, useEffect } from "react";
import FileUpload from "../components/FileUpload.jsx";
import TailoredOutput from "../components/TailoredOutput.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import useResumeTailor from "../hooks/useResumeTailor.js";
import DescriptionIcon from "@mui/icons-material/Description";

const ResumeTailorPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [resumeContent, setResumeContent] = useState("");
  const [jobDesc, setJobDesc] = useState("");
  const [model, setModel] = useState("GEMMA_4_31B_IT");
  const {
    output,
    suggestions,
    companyName,
    loading,
    error,
    tailorResume,
    outreachMessage,
    setOutreachMessage,
    outreachLoading,
    outreachError,
    generateOutreach,
  } = useResumeTailor();
  const [showInputs, setShowInputs] = useState(true);

  const [outreachRecipient, setOutreachRecipient] = useState("recruiter");
  const [outreachChannel, setOutreachChannel] = useState("email");
  const [copied, setCopied] = useState(false);


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

  const handleCopy = () => {
    if (!outreachMessage) return;
    const textToCopy = outreachMessage.subject
      ? `Subject: ${outreachMessage.subject}\n\n${outreachMessage.body}`
      : outreachMessage.body;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
            <option value="GEMMA_4_31B_IT">Gemma 4 31B IT</option>
            <option value="DEEPSEEK_V3_0324">DeepSeek: V3 0324</option>
            <option value="QWEN3_235B_A22B">Qwen3 235B A22B</option>
            <option value="Z.AI_GLM_4_5_AIR">Z.AI: GLM 4.5 Air</option>
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

              {/* Outreach Generation Panel */}
              {output && (
                <div className="outreach-panel mt-6">
                  <div className="outreach-header">
                    <span className="label">Outreach Message</span>
                    <div className="flex gap-2">
                      <select
                        value={outreachRecipient}
                        onChange={(e) => setOutreachRecipient(e.target.value)}
                        className="outreach-select"
                        disabled={outreachLoading}
                      >
                        <option value="recruiter">Recruiter</option>
                        <option value="ceo">CEO</option>
                      </select>
                      <select
                        value={outreachChannel}
                        onChange={(e) => setOutreachChannel(e.target.value)}
                        className="outreach-select"
                        disabled={outreachLoading}
                      >
                        <option value="email">Email</option>
                        <option value="inmail">InMail</option>
                      </select>
                    </div>
                  </div>

                  <div className="outreach-body mt-3">
                    {outreachLoading ? (
                      <div className="flex justify-center items-center py-6 gap-2 text-muted text-sm">
                        <LoadingSpinner /> Generating message…
                      </div>
                    ) : outreachError ? (
                      <div className="toast toast-error mt-2">{outreachError}</div>
                    ) : outreachMessage ? (
                      <div className="outreach-content space-y-3">
                        {outreachMessage.subject && (
                          <div className="subject-line">
                            <span className="text-muted font-bold text-xs uppercase mr-2">Subject:</span>
                            <span className="text-sm">{outreachMessage.subject}</span>
                          </div>
                        )}
                        <textarea
                          className="textarea text-sm font-sans"
                          rows={10}
                          value={outreachMessage.body}
                          onChange={(e) =>
                            setOutreachMessage({ ...outreachMessage, body: e.target.value })
                          }
                          placeholder="Generated message..."
                        />
                        <div className="flex justify-between items-center mt-2">
                          <button
                            onClick={() => generateOutreach(output, jobDesc, outreachRecipient, outreachChannel)}
                            className="btn btn-secondary text-xs"
                            style={{ padding: "6px 12px" }}
                            disabled={outreachLoading}
                          >
                            Regenerate
                          </button>
                          <button
                            onClick={handleCopy}
                            className="btn btn-secondary text-xs"
                            style={{ padding: "6px 12px" }}
                          >
                            {copied ? "Copied!" : "Copy Message"}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-center py-2">
                        <button
                          onClick={() => generateOutreach(output, jobDesc, outreachRecipient, outreachChannel)}
                          className="btn btn-primary w-full text-xs"
                          disabled={outreachLoading}
                        >
                          Generate Outreach Message
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Editor + Preview Panels */}
        <TailoredOutput output={output} resumeContent={resumeContent} loading={loading} companyName={companyName} />
      </main>

      <footer className="app-footer">
        &copy; {new Date().getFullYear()} <span className="font-semibold">Resume Tailor AI</span>
      </footer>
    </div>
  );
};

export default ResumeTailorPage;


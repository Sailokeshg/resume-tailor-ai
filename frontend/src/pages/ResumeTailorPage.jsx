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

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (evt) => {
      setResumeContent(evt.target.result);
    };
    reader.readAsText(file);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!resumeContent || !jobDesc) {
      return;
    }
    tailorResume(resumeContent, jobDesc);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-purple-200 flex flex-col items-center justify-center py-8 px-2">
      <div className="resume-card w-full max-w-5xl">
        <div className="resume-card__header flex items-center gap-3">
          <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 text-white shadow-lg">
            <DescriptionIcon fontSize="large" />
          </span>
          <div>
            <h1 className="resume-title">Resume Tailor AI</h1>
            <p className="text-white/80 text-sm leading-tight">Smart tailoring for LaTeX resumes</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="card-body">
          <section className="editor-pane">
            <FileUpload onFileSelect={handleFileSelect} loading={loading} />
            <div className="mt-6">
              <label className="block text-base font-semibold text-gray-700 mb-2 tracking-wide">
                Job Description
              </label>
              <textarea
                className="editor-textarea"
                placeholder="Paste the job description here..."
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                disabled={loading}
              />
            </div>
          </section>

          {error && (
            <div className="col-span-2 mt-2 text-red-700 bg-red-100 rounded-xl px-4 py-2 text-center font-semibold shadow-md border border-red-200">
              {error}
            </div>
          )}

          {output && (
            <div className="col-span-2 mt-4">
              <TailoredOutput output={output} />
              {output && (
                <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                  <h3 className="font-semibold text-yellow-800 mb-2">Improvements Summary</h3>
                  {improvementsSummary ? (
                    <p className="whitespace-pre-wrap text-yellow-900">{improvementsSummary}</p>
                  ) : (
                    <p className="text-yellow-900 italic">No improvements summary provided by the model.</p>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="resume-card__footer col-span-2">
            <button
              type="submit"
              disabled={loading || !resumeContent || !jobDesc}
              className="cta-button"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <LoadingSpinner /> Tailoring...
                </span>
              ) : (
                "Tailor Resume"
              )}
            </button>
          </div>
        </form>
      </div>

      <footer className="mt-10 text-gray-400 text-sm drop-shadow-lg">
        &copy; {new Date().getFullYear()} {""}
        <span className="font-semibold text-blue-500">Resume Tailor AI</span>. All rights reserved.
      </footer>
    </div>
  );
};

export default ResumeTailorPage;

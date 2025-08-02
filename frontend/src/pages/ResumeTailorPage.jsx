import React, { useState } from "react";
import FileUpload from "../components/FileUpload.jsx";
import JobDescriptionInput from "../components/JobDescriptionInput.jsx";
import TailoredOutput from "../components/TailoredOutput.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import useResumeTailor from "../hooks/useResumeTailor.js";
import DescriptionIcon from "@mui/icons-material/Description";

const ResumeTailorPage = () => {
  const [resume, setResume] = useState("");
  const [jobDesc, setJobDesc] = useState("");
  const { output, loading, error, tailorResume } = useResumeTailor();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => setResume(evt.target.result);
    reader.readAsText(file);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    tailorResume(resume, jobDesc);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-purple-200 flex flex-col items-center justify-center py-8 px-2">
      <div className="w-full max-w-lg bg-white/80 rounded-3xl shadow-2xl border border-blue-200 backdrop-blur-lg p-0 overflow-hidden">
        {/* Card Header with Icon */}
        <div className="bg-gradient-to-r from-blue-100 to-purple-100 px-8 py-6 border-b border-blue-100 flex items-center gap-3">
          <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 text-white shadow-lg">
            <DescriptionIcon fontSize="large" />
          </span>
          <span className="text-2xl font-extrabold text-gray-800 tracking-tight ml-2">
            Resume Tailor AI
          </span>
        </div>
        <form onSubmit={handleSubmit} className="px-8 py-8 flex flex-col gap-7">
          {/* Upload Resume Section */}
          <div>
            <label className="block text-base font-semibold text-gray-700 mb-2 tracking-wide">
              Upload Resume
            </label>
            <div className="flex items-center gap-4">
              {/* Custom file input styling */}
              <label className="flex items-center px-4 py-2 bg-gradient-to-r from-blue-400 to-purple-400 text-white rounded-lg shadow cursor-pointer hover:from-blue-500 hover:to-purple-500 transition-all duration-150">
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"
                  />
                </svg>
                <span className="font-medium">Choose File</span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <span className="text-sm text-gray-500 font-medium truncate max-w-[120px]">
                {resume ? "File loaded" : "No file chosen"}
              </span>
            </div>
          </div>
          {/* Job Description Section */}
          <div>
            <label className="block text-base font-semibold text-gray-700 mb-2 tracking-wide">
              Job Description
            </label>
            <textarea
              className="w-full min-h-[100px] rounded-lg border border-blue-200 bg-white/80 px-4 py-3 text-gray-700 font-medium shadow focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all resize-none placeholder-gray-400"
              placeholder="Paste the job description here..."
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
            />
          </div>
          {/* Tailor Resume Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold text-lg shadow-md hover:from-blue-600 hover:to-purple-600 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <LoadingSpinner size={5} /> Tailoring...
              </span>
            ) : (
              "Tailor Resume"
            )}
          </button>
          {/* Error and Output */}
          {error && (
            <div className="mt-4 text-red-700 bg-red-100 rounded-xl px-4 py-2 text-center font-semibold shadow-md border border-red-200 animate-pulse">
              {error}
            </div>
          )}
          {output && (
            <div className="mt-8">
              <TailoredOutput output={output} />
            </div>
          )}
        </form>
      </div>
      <footer className="mt-10 text-gray-400 text-sm drop-shadow-lg">
        &copy; {new Date().getFullYear()}{" "}
        <span className="font-semibold text-blue-500">Resume Tailor AI</span>.
        All rights reserved.
      </footer>
    </div>
  );
};

export default ResumeTailorPage;

import { useState } from "react";
import api from "../services/api";

export default function useResumeTailor() {
  const [output, setOutput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [improvementsSummary, setImprovementsSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [outreachMessage, setOutreachMessage] = useState(null);
  const [outreachLoading, setOutreachLoading] = useState(false);
  const [outreachError, setOutreachError] = useState("");
  const [progressSteps, setProgressSteps] = useState([]);

  const generateOutreach = async (resume, jobDesc, recipient, channel, provider) => {
    setOutreachLoading(true);
    setOutreachError("");
    try {
      const res = await api.generateOutreach(resume, jobDesc, recipient, channel, provider);
      setOutreachMessage(res);
    } catch (err) {
      setOutreachError(err.message || "Failed to generate outreach message.");
    } finally {
      setOutreachLoading(false);
    }
  };

  const tailorResume = async (resume, jobDesc, model, provider) => {
    setLoading(true);
    setError("");
    setOutput("");
    setSuggestions([]);
    setImprovementsSummary("");
    setCompanyName("");
    setOutreachMessage(null);
    setOutreachError("");
    setProgressSteps([]);

    try {
      const res = await api.tailorResumeSSE(
        resume,
        jobDesc,
        model,
        provider,
        (eventType, parsedData) => {
          if (eventType === "progress") {
            setProgressSteps((prev) => {
              const existingIndex = prev.findIndex((s) => s.step === parsedData.step);
              if (existingIndex >= 0) {
                const next = [...prev];
                next[existingIndex] = { ...next[existingIndex], ...parsedData };
                return next;
              } else {
                return [...prev, parsedData];
              }
            });
          } else if (eventType === "chunk") {
            // Append incoming tokens to output for real-time typing effect
            setOutput((prev) => prev + (parsedData.text || ""));
          }
        }
      );
      const raw = res.tailored_resume || "";

      const removeThinkBlocks = (text) => {
        try {
          // Remove any chain-of-thought blocks like <think> ... </think>
          return text.replace(/<think>[\s\S]*?<\/think>/gi, "");
        } catch (_) {
          return text;
        }
      };

      const stripCodeFences = (text) => {
        const fenceOpen = text.match(/^```[a-zA-Z]*\n/);
        if (fenceOpen) {
          const closingIndex = text.lastIndexOf("```");
          if (closingIndex > fenceOpen[0].length) {
            return text.slice(fenceOpen[0].length, closingIndex);
          }
        }
        return text;
      };

      const cleaned = stripCodeFences(removeThinkBlocks(raw)).trim();
      const endTag = "\\end{document}";
      const endDocIndex = cleaned.indexOf(endTag);

      if (endDocIndex !== -1) {
        const end = endDocIndex + endTag.length;
        const latexPart = cleaned.slice(0, end).trim();
        const trailing = cleaned.slice(end).trim();
        setOutput(latexPart);
        setImprovementsSummary(trailing);
      } else {
        // If no explicit end of document found, keep entire content as output and no improvements summary
        setOutput(cleaned);
        setImprovementsSummary("");
      }

      // Preserve original suggestions array (not shown in UI for improvements summary)
      setSuggestions(res.suggestions || []);
      setCompanyName(res.company_name || "");
    } catch (err) {
      setError(err.message || "Failed to tailor resume.");
    } finally {
      setLoading(false);
      setProgressSteps([]);
    }
  };

  return {
    output,
    suggestions,
    improvementsSummary,
    companyName,
    loading,
    error,
    progressSteps,
    tailorResume,
    outreachMessage,
    setOutreachMessage,
    outreachLoading,
    outreachError,
    generateOutreach,
  };
}

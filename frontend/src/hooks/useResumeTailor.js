import { useState } from "react";
import api from "../services/api";

export default function useResumeTailor() {
  const [output, setOutput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [improvementsSummary, setImprovementsSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tailorResume = async (resume, jobDesc, model) => {
    setLoading(true);
    setError("");
    setOutput("");
    setSuggestions([]);
    setImprovementsSummary("");

    try {
      const res = await api.tailorResume(resume, jobDesc, model);
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
    } catch (err) {
      setError("Failed to tailor resume.");
    } finally {
      setLoading(false);
    }
  };

  return { output, suggestions, improvementsSummary, loading, error, tailorResume };
}

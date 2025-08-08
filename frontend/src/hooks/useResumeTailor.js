import { useState } from "react";
import api from "../services/api";

export default function useResumeTailor() {
  const [output, setOutput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tailorResume = async (resume, jobDesc) => {
    setLoading(true);
    setError("");
    setOutput("");
    setSuggestions([]);

    try {
      const res = await api.tailorResume(resume, jobDesc);
      setOutput(res.tailored_resume);
      setSuggestions(res.suggestions || []);
    } catch (err) {
      setError("Failed to tailor resume.");
    } finally {
      setLoading(false);
    }
  };

  return { output, suggestions, loading, error, tailorResume };
}

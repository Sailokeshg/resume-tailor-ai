import { useState } from "react";
import api from "../services/api";

export default function useResumeTailor() {
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tailorResume = async (resume, jobDesc) => {
    setLoading(true);
    setError("");
    setOutput("");
    console.log("inside tailorResume with resume:", resume, "and jobDesc:", jobDesc);
    try {
      const res = await api.tailorResume(resume, jobDesc);
      setOutput(res.tailored_resume);
    } catch (err) {
      setError("Failed to tailor resume.");
    } finally {
      setLoading(false);
    }
  };

  return { output, loading, error, tailorResume };
}

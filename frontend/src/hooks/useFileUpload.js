import { useState } from "react";

export default function useFileUpload() {
  const [fileContent, setFileContent] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => setFileContent(evt.target.result);
    reader.readAsText(file);
  };

  return { fileContent, handleFileChange };
}

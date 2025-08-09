const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/v1/resume/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload resume');
    }

    return response.json();
  }

  async tailorResume(resumeContent, jobDescription, model) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume: resumeContent,
        job_description: jobDescription,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to tailor resume');
    }

    return response.json();
  }

  async compilePdf(latexContent) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/compile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/pdf'
      },
      body: JSON.stringify({ resume: latexContent }),
    });

    if (!response.ok) {
      // Try to parse error body for message
      let message = 'Failed to compile PDF';
      try {
        const err = await response.json();
        if (err?.detail) message = err.detail;
      } catch (_) {}
      throw new Error(message);
    }

    const blob = await response.blob();
    return blob;
  }

  async analyzeMatch(resumeContent, jobDescription) {
    const response = await fetch(`${this.baseURL}/api/v1/resume/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume: resumeContent,
        job_description: jobDescription,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze match');
    }

    return response.json();
  }
}

export default new ApiService();

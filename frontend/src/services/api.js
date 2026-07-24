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

  async tailorResume(resumeContent, jobDescription, model, provider) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume: resumeContent,
        job_description: jobDescription,
        model,
        provider,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to tailor resume');
    }

    return response.json();
  }

  async tailorResumeSSE(resumeContent, jobDescription, model, provider, onProgress) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        resume: resumeContent,
        job_description: jobDescription,
        model,
        provider,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to tailor resume');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || "";
      
      for (const part of parts) {
        if (!part.trim()) continue;
        
        let eventType = "message";
        let dataStr = "";
        
        const lines = part.split('\n');
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.slice(6).trim();
          }
        }
        
        if (dataStr) {
          try {
            const parsedData = JSON.parse(dataStr);
            if (eventType === 'error') {
              throw new Error(parsedData.detail || parsedData.message || 'Error during streaming');
            }
            if (eventType === 'result') {
              return parsedData;
            }
            if (onProgress) {
              onProgress(eventType, parsedData);
            }
          } catch (e) {
            if (eventType === 'error') throw e;
            console.error("SSE parse error", e, dataStr);
          }
        }
      }
    }
    
    throw new Error('Stream ended without a result event');
  }

  async compilePdf(latexContent, signal) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/compile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/pdf'
      },
      signal,
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

  async generateOutreach(resumeContent, jobDescription, recipient, channel, provider) {
    const response = await fetch(`${this.baseURL}/api/v1/tailor/outreach`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume: resumeContent,
        job_description: jobDescription,
        recipient,
        channel,
        provider,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate outreach');
    }

    return response.json();
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

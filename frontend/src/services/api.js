import axios from "axios";

const api = {
  tailorResume: async (resume, jobDesc) => {
    const res = await axios.post("/api/v1/tailor/", {
      resume,
      job_description: jobDesc,
    });
    return res.data;
  },
};

export default api;

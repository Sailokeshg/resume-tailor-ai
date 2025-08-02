import axios from "axios";

export default function useAPI() {
  const callAPI = async (url, method = "get", data = null) => {
    const res = await axios({ url, method, data });
    return res.data;
  };
  return { callAPI };
}

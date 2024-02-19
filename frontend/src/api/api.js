import axios from "axios";

const baseURL = "https://www.ocf.berkeley.edu/~lqi/instalily-server/query"
// const baseURL = "https://2e3a-2607-f140-8801-00-1-25.ngrok-free.app/query"

export const getAIMessage = async (userQuery) => {

  const response = await axios.post(baseURL, {
    query: userQuery,
    history: ["history0", "history1"]
  })
  console.log(response)
  const message = {
    role: "assistant",
    content: response.data.query
  }
    // {
    //   role: "assistant",
    //   content: "Connect your backend here...."
    // }

  return message;
};

import axios from "axios";

const baseURL = "https://www.ocf.berkeley.edu/~lqi/instalily-server/api/v1/query"

export const getAIMessage = async (userQuery, history, serverKey) => {
  console.log(userQuery, history)

  const response = await axios.post(baseURL, {
    query: userQuery,
    history: history,
    serverKey: serverKey
  })

  console.log(response)

  const message = {
    role: "assistant",
    content: response.data.response
  }

  return message;
};

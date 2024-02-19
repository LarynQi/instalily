import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";
import ClipLoader from "react-spinners/ClipLoader";

function ChatWindow({serverKey}) {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi, I'm a Q&A chatbot for PartSelect.com. Please be patient as I come up with my responses. How can I help you today?"
  }];

  const [messages,setMessages] = useState(defaultMessage)
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
      scrollToBottom();
  }, [isLoading]);

  const handleSend = async (input) => {
    setIsLoading(true);
    try {
      if (input.trim() !== "") {
        // Set user message
        setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
        setInput("");
        // Call API & set assistant message
        const newMessage = await getAIMessage(input, messages, serverKey);
        setMessages(prevMessages => [...prevMessages, newMessage]);
      }
      setIsLoading(false);
    } catch (e) {
      setIsLoading(false);
      const newMessage = {
        role: "assistant",
        content: `Sorry, a client-side error has occurred. Please try again later.\n${e.toString()}`
      }
      setMessages(prevMessages => [...prevMessages, newMessage]);
    }
  };

  return (
      <div className="messages-container">
          {messages.map((message, index) => (
              <div key={index} className={`${message.role}-message-container`}>
                  {message.content && (
                      <div className={`message ${message.role}-message`}>
                          <div dangerouslySetInnerHTML={{__html: marked(message.content).replace(/<p>|<\/p>/g, "")}}></div>
                      </div>
                  )}
              </div>
          ))}
          <ClipLoader 
            loading={isLoading}
            color="#36d7b7"
          />
          <div ref={messagesEndRef} />
          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !isLoading) {
                  handleSend(input);
                  e.preventDefault();
                }
              }}
              rows="3"
            />
            <button className="send-button" onClick={(e) => !isLoading ? handleSend(input) : null}>
              Send
            </button>
          </div>
      </div>
);
}

export default ChatWindow;

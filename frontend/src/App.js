import React, { useState } from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState(false);

  if (!submitted) {
    return (
    <div className="flex-container">
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Paste key here"
        onKeyPress={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            setSubmitted(true);
            e.preventDefault();
          }
        }}
      />
      <button className="send-button" onClick={(e) => setSubmitted(true)}>
        Submit
      </button>
    </div>)
  } else {
    return (
      <div className="App">
        <div className="heading">
          Instalily Case Study
        </div>
          <ChatWindow 
            serverKey={input}
          />
      </div>
    );
  }
}

export default App;

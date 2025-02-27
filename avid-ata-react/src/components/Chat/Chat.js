import React, { useState } from "react";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import "./Chat.css";

const Chat = () => {
  const [messages, setMessages] = useState([]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const newMessage = { text, sender: "user" };
    setMessages([...messages, newMessage]);

    // Simula una risposta dal backend
    setTimeout(() => {
      const botReply = { text: "Risposta dal backend...", sender: "bot" };
      setMessages((prev) => [...prev, botReply]);
    }, 1000);
  };

  return (
    <div className="chat-container">
      <h3>Chatbot</h3>
      <MessageList messages={messages} />
      <MessageInput sendMessage={sendMessage} />
    </div>
  );
};

export default Chat;
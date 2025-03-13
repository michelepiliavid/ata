import React, { useState } from "react";
import "./Chat.css";

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return; // Evita di inviare messaggi vuoti

    const userMessage = { text: input, sender: "user" };
    setMessages([...messages, userMessage]); // Aggiunge il messaggio utente alla chat

    try {
      const response = await fetch(
        `http://localhost:5000/rest/conversation/get_simple_answer?prompt=${encodeURIComponent(input)}`
      );

      if (!response.ok) throw new Error("Errore nella richiesta");

      const data = await response.json();
      const botMessage = { text: data.answer || "Nessuna risposta disponibile", sender: "bot" };

      setMessages((prevMessages) => [...prevMessages, botMessage]); // Aggiunge la risposta del bot
    } catch (error) {
      console.error("Errore nella richiesta API:", error);
      setMessages((prevMessages) => [...prevMessages, { text: "Errore nel server", sender: "bot" }]);
    }

    setInput(""); // Resetta l'input dopo l'invio
  };

  return (
    <div className="chat-container">
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Scrivi un messaggio..."
        />
        <button onClick={sendMessage}>Invia</button>
      </div>
    </div>
  );
};

export default Chat;

import { useState, useEffect } from "react";
import Main from "./components/Main";
import Footer from "./components/Footer";
// src/App.jsx
export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("logged_in") === "1") {
      setLoggedIn(true);
    }
  }, []);

  const handleSpotifyLogin = () => {
    window.location.href = "https://recapify-api.onrender.com/login";
  };

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">
      <Main loggedIn={loggedIn} handleSpotifyLogin={handleSpotifyLogin} />
      <Footer />
    </div>
  );
}

// App.js

import React, { useState } from 'react';
import LoginSignupPage from './components/LoginSignupPage';
import ChatPage from './components/ChatPage';

function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);

  const handleLogin = (token, user) => {
    setToken(token);
    setUser(user);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    sessionStorage.removeItem('session_id');
  };

  if (!token) {
    return <LoginSignupPage onLogin={handleLogin} />;
  }

  return <ChatPage token={token} user={user} onLogout={handleLogout} />;
}

export default App;
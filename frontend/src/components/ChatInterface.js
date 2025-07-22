
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Box, TextField, IconButton, Typography, CircularProgress, InputAdornment } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import EmojiEmotionsIcon from '@mui/icons-material/EmojiEmotions';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ChatBubble from './ChatBubble';

const BACKEND_BASE_URL = process.env.REACT_APP_API_BASE_URL;

function getSessionId() {
  let sessionId = sessionStorage.getItem('session_id');
  if (!sessionId) {
    if (window.crypto && window.crypto.randomUUID) {
      sessionId = window.crypto.randomUUID();
    } else {
      sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    }
    sessionStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}

function ChatInterface({ token, user, showNotification }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage = { role: 'user', content: input, timestamp };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const sessionId = getSessionId();
      const res = await axios.post(`${BACKEND_BASE_URL}/chat`, {
        message: input,
        session_id: sessionId
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessages(msgs => [
        ...msgs,
        {
          role: 'assistant',
          content: res.data.response,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      showNotification('Error sending message', 'error');
    }
    setLoading(false);
  };

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'white',
      }}
    >
      {/* Messages Area with Updated Padding */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          px: { xs: 4, sm: 6 },  // Horizontal padding
          py: 4,                 // Vertical padding
          '&::-webkit-scrollbar': {
            width: '6px'
          },
          '&::-webkit-scrollbar-track': {
            bgcolor: 'transparent'
          },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: '#ddd',
            borderRadius: '3px'
          },
          // Add container width constraint
          maxWidth: '900px',
          mx: 'auto',
          width: '100%'
        }}
      >
        {messages.length === 0 && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              flexDirection: 'column'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: '#74b9ff',
                mb: 1,
                fontWeight: 600
              }}
            >
              Hello! I'm your Employee Self Service Bot
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: '#636e72',
                textAlign: 'center'
              }}
            >
              Ask me anything about HR policies, leave requests, or general questions
            </Typography>
          </Box>
        )}

        {messages.map((msg, idx) => (
          <ChatBubble key={idx} message={msg} isUser={msg.role === 'user'} user={user} />
        ))}

        {loading && (
          <Box display="flex" justifyContent="flex-start" mb={2} alignItems="center">
            <Box
              sx={{
                p: 2,
                borderRadius: '20px 20px 20px 4px',
                bgcolor: '#f8f9fa',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <CircularProgress size={16} sx={{ color: '#6c5ce7' }} />
              <Typography variant="body2" sx={{ color: '#636e72' }}>
                Typing...
              </Typography>
            </Box>
          </Box>
        )}

        <div ref={chatEndRef} />
      </Box>

      {/* Input Area with Updated Padding */}
      <Box
        sx={{
          borderTop: '1px solid #f1f3f4',
          bgcolor: 'white',
          maxWidth: '900px',
          mx: 'auto',
          width: '100%'
        }}
      >
        <Box
          sx={{
            p: { xs: 2, sm: 3 },
            px: { xs: 4, sm: 6 },
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            <TextField
              fullWidth
              placeholder="Message to Employee Self Service Bot..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              disabled={loading}
              multiline
              maxRows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '24px',
                  bgcolor: '#f8f9fa',
                  border: 'none',
                  '&:hover': {
                    bgcolor: '#f1f3f4'
                  },
                  '&.Mui-focused': {
                    bgcolor: 'white',
                    boxShadow: '0 2px 8px rgba(108, 92, 231, 0.15)'
                  },
                  '& fieldset': {
                    border: 'none'
                  }
                },
                '& .MuiInputBase-input': {
                  py: 1.5,
                  px: 2
                }
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <IconButton size="small" sx={{ color: '#636e72' }}>
                      <EmojiEmotionsIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton size="small" sx={{ color: '#636e72' }}>
                      <AttachFileIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />

            <IconButton
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              sx={{
                bgcolor: input.trim() ? '#6c5ce7' : '#ddd',
                color: 'white',
                '&:hover': {
                  bgcolor: input.trim() ? '#5a4fcf' : '#ccc'
                },
                '&.Mui-disabled': {
                  bgcolor: '#ddd',
                  color: 'white'
                },
                width: 44,
                height: 44
              }}
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default ChatInterface;
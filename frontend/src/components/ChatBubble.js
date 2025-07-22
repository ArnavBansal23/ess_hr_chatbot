import React from 'react';
import { Box, Typography, Avatar } from '@mui/material';

function ChatBubble({ message, isUser, user }) {
  return (
    <Box
      display="flex"
      justifyContent={isUser ? "flex-end" : "flex-start"}
      mb={2}
      alignItems="flex-end"
    >
      {!isUser && (
        <Avatar
          sx={{
            mr: 1,
            bgcolor: '#6c5ce7',
            width: 32,
            height: 32,
            fontSize: '14px'
          }}
        >
          🤖
        </Avatar>
      )}

      <Box
        sx={{
          maxWidth: '50%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start'
        }}
      >
        <Box
          sx={{
            p: 2,
            borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
            bgcolor: isUser ? '#6c5ce7' : '#f8f9fa',
            color: isUser ? 'white' : '#2d3436',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            position: 'relative',
            wordBreak: 'break-word'
          }}
        >
          <Typography
            variant="body1"
            sx={{
              fontSize: '14px',
              lineHeight: 1.4,
              margin: 0
            }}
          >
            {message.content}
          </Typography>
        </Box>

        <Typography
          variant="caption"
          sx={{
            color: '#74b9ff',
            fontSize: '11px',
            mt: 0.5,
            px: 1
          }}
        >
          {message.timestamp}
        </Typography>
      </Box>

      {isUser && (
        <Avatar
          sx={{
            ml: 1,
            bgcolor: '#00b894',
            width: 32,
            height: 32,
            fontSize: '14px'
          }}
        >
          {user?.email?.[0]?.toUpperCase() || "U"}
        </Avatar>
      )}
    </Box>
  );
}

export default ChatBubble;



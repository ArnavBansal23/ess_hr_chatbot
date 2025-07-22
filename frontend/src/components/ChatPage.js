import React, { useState } from 'react';
import { Box, Typography, IconButton, Avatar,} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import SettingsIcon from '@mui/icons-material/Settings';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import ChatInterface from './ChatInterface';

function ChatPage({ token, user, onLogout }) {
  const [darkMode, setDarkMode] = useState(false);

  return (
    <Box sx={{
      display: 'flex',
      height: '100vh',
      bgcolor: '#f8f9fa',
      overflow: 'hidden'
    }}>
      {/* Left Sidebar */}
      <Box sx={{
        width: 70,
        bgcolor: 'white',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 2,
        borderRight: '1px solid #f1f3f4',
        boxShadow: '2px 0 8px rgba(0,0,0,0.04)'
      }}>
        {/* Logo */}
        <Box sx={{
          width: 40,
          height: 40,
          bgcolor: '#6c5ce7',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3
        }}>
          <Typography sx={{
            color: 'white',
            fontSize: '16px',
            fontWeight: 'bold'
          }}>
            E
          </Typography>
        </Box>

        {/* Navigation Icons */}
        <IconButton
          sx={{
            mb: 2,
            width: 44,
            height: 44,
            bgcolor: '#f8f9fa',
            '&:hover': { bgcolor: '#e9ecef' }
          }}
        >
          <ChatBubbleOutlineIcon sx={{ color: '#6c5ce7' }} />
        </IconButton>

        <IconButton
          sx={{
            mb: 2,
            width: 44,
            height: 44,
            '&:hover': { bgcolor: '#f8f9fa' }
          }}
        >
          <MenuIcon sx={{ color: '#636e72' }} />
        </IconButton>

        <IconButton
          sx={{
            mb: 2,
            width: 44,
            height: 44,
            '&:hover': { bgcolor: '#f8f9fa' }
          }}
        >
          <SettingsIcon sx={{ color: '#636e72' }} />
        </IconButton>

        <Box sx={{ flexGrow: 1 }} />

        {/* Theme Toggle */}
        <IconButton
          onClick={() => setDarkMode(!darkMode)}
          sx={{
            mb: 2,
            width: 44,
            height: 44,
            '&:hover': { bgcolor: '#f8f9fa' }
          }}
        >
          {darkMode ?
            <LightModeIcon sx={{ color: '#636e72' }} /> :
            <DarkModeIcon sx={{ color: '#636e72' }} />
          }
        </IconButton>

        {/* User Avatar */}
        <Avatar
          sx={{
            width: 36,
            height: 36,
            bgcolor: '#00b894',
            mb: 2,
            fontSize: '14px'
          }}
        >
          {user?.email?.[0]?.toUpperCase() || "U"}
        </Avatar>

        {/* Logout */}
        <IconButton
          onClick={onLogout}
          sx={{
            width: 44,
            height: 44,
            color: '#e17055',
            '&:hover': {
              bgcolor: '#ffeaea',
              color: '#d63031'
            }
          }}
        >
          <LogoutIcon />
        </IconButton>
      </Box>

      {/* Main Chat Container */}
      <Box sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'white',
        position: 'relative'
      }}>
        {/* Header */}
        <Box sx={{
          p: 3,
          borderBottom: '1px solid #f1f3f4',
          bgcolor: 'white'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{
              bgcolor: '#6c5ce7',
              width: 40,
              height: 40,
              fontSize: '14px'
            }}>
              ESS
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{
                fontWeight: 600,
                color: '#2d3436',
                fontSize: '18px'
              }}>
                Employee Self Service Bot 🤖
              </Typography>
              <Typography variant="body2" sx={{
                color: '#74b9ff',
                fontSize: '13px'
              }}>
                Hello! I'm your Personal HR Assistant
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Chat Interface */}
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <ChatInterface
            token={token}
            user={user}
            showNotification={(msg, type) => console.log(msg, type)}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default ChatPage;

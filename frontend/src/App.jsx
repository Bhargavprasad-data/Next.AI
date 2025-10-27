import React, { useState, useEffect } from 'react';
import { Box, ThemeProvider, createTheme, CssBaseline, CircularProgress } from '@mui/material';
import Login from './components/Login';
import ChatInterface from './components/ChatInterface';
import { authService } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6A6ADF',
    },
    secondary: {
      main: '#8A6AE0',
    },
    background: {
      default: '#343541',
      paper: '#202123',
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const handleLogin = async (userData) => {
    const token = await authService.login(userData.email, userData.password);
    localStorage.setItem('token', token);
    const currentUser = await authService.getCurrentUser();
    setUser(currentUser);
    setIsAuthenticated(true);
  };

  const handleRegister = async (userData) => {
    await authService.register(userData);
    const token = await authService.login(userData.email, userData.password);
    localStorage.setItem('token', token);
    const currentUser = await authService.getCurrentUser();
    setUser(currentUser);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
          bgcolor="#343541"
        >
          <CircularProgress sx={{ color: '#6A6ADF' }} />
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box minHeight="100vh" bgcolor="#343541">
        {isAuthenticated ? (
          <ChatInterface user={user} onLogout={handleLogout} />
        ) : (
          <Login onLogin={handleLogin} onRegister={handleRegister} />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;


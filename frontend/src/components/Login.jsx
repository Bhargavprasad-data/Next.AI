import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import RobotIcon from './RobotIcon';

function Login({ onLogin, onRegister }) {
  const [mode, setMode] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (mode === 0) {
        await onLogin({ email, password });
      } else {
        if (!username) {
          setError('Username is required');
          return;
        }
        await onRegister({ email, password, username });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #16213e 100%)',
        position: 'relative',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        py: 4,
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(147, 51, 234, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 60% 70%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)
          `,
          zIndex: 1,
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            linear-gradient(45deg, transparent 30%, rgba(59, 130, 246, 0.05) 50%, transparent 70%),
            linear-gradient(-45deg, transparent 30%, rgba(147, 51, 234, 0.05) 50%, transparent 70%)
          `,
          zIndex: 1,
        },
      }}
    >
      <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 2 }}>
        <Paper
          elevation={0}
          sx={{
            p: 4,
            width: '100%',
            background: 'rgba(31, 31, 58, 0.9)',
            backdropFilter: 'blur(10px)',
            borderRadius: 2,
            border: '1px solid rgba(160, 128, 224, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          }}
        >
          <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
            <RobotIcon size={40} color="#A080E0" />
            <Typography
              variant="h4"
              component="h1"
              sx={{
                color: '#A080E0',
                fontWeight: 600,
                fontSize: '28px',
              }}
            >
              Next.AI
            </Typography>
          </Box>

          <Tabs 
            value={mode} 
            onChange={(e, v) => setMode(v)} 
            sx={{ 
              mb: 3,
              '& .MuiTab-root.Mui-selected': {
                color: '#A080E0',
              },
              '& .MuiTab-root:not(.Mui-selected)': {
                color: '#B0B0C0',
              },
              '& .MuiTab-root': {
                fontWeight: 600,
                textTransform: 'uppercase',
              },
              '& .MuiTabs-indicator': {
                backgroundColor: '#A080E0',
              },
            }}
          >
            <Tab label="Login" />
            <Tab label="Register" />
          </Tabs>

          {error && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                backgroundColor: '#2A2A45',
                color: '#E0E0E0',
                '& .MuiAlert-icon': {
                  color: '#ff6b6b',
                },
              }}
            >
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            {mode === 1 && (
              <TextField
                fullWidth
                label="Username"
                variant="outlined"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                margin="normal"
                required
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#2A2A45',
                    color: '#E0E0E0',
                    '& fieldset': {
                      borderColor: '#606070',
                    },
                    '&:hover fieldset': {
                      borderColor: '#A080E0',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#A080E0',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#E0E0E0',
                  },
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#A080E0',
                  },
                }}
              />
            )}
            <TextField
              fullWidth
              label="Email"
              variant="outlined"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              required
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#2A2A45',
                  color: '#E0E0E0',
                  '& fieldset': {
                    borderColor: '#606070',
                  },
                  '&:hover fieldset': {
                    borderColor: '#A080E0',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#A080E0',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: '#E0E0E0',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#A080E0',
                },
              }}
            />
            <TextField
              fullWidth
              label="Password"
              variant="outlined"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#2A2A45',
                  color: '#E0E0E0',
                  '& fieldset': {
                    borderColor: '#606070',
                  },
                  '&:hover fieldset': {
                    borderColor: '#A080E0',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#A080E0',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: '#E0E0E0',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#A080E0',
                },
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{
                mt: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #7060E0 0%, #C060E0 100%)',
                textTransform: 'uppercase',
                fontWeight: 600,
                borderRadius: 1,
                '&:hover': {
                  background: 'linear-gradient(135deg, #8060E0 0%, #D060E0 100%)',
                },
              }}
            >
              {mode === 0 ? 'Login' : 'Register'}
            </Button>
          </form>
        </Paper>
      </Container>
      
      {/* Futuristic network background */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1,
          pointerEvents: 'none',
        }}
      >
        {/* Jellyfish silhouettes in upper half */}
        <Box
          sx={{
            position: 'absolute',
            left: '15%',
            top: '10%',
            width: 60,
            height: 80,
            background: 'radial-gradient(ellipse at center, rgba(147, 51, 234, 0.3) 0%, transparent 70%)',
            borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
            animation: 'float 6s ease-in-out infinite',
            '&::before': {
              content: '""',
              position: 'absolute',
              bottom: -20,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 2,
              height: 30,
              background: 'linear-gradient(to bottom, rgba(147, 51, 234, 0.6), transparent)',
              borderRadius: 1,
            },
            '&::after': {
              content: '""',
              position: 'absolute',
              bottom: -15,
              left: '30%',
              width: 1,
              height: 25,
              background: 'linear-gradient(to bottom, rgba(147, 51, 234, 0.4), transparent)',
              borderRadius: 1,
            },
            '@keyframes float': {
              '0%, 100%': { transform: 'translateY(0px)' },
              '50%': { transform: 'translateY(-10px)' },
            },
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            left: '45%',
            top: '15%',
            width: 50,
            height: 70,
            background: 'radial-gradient(ellipse at center, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
            borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
            animation: 'float 8s ease-in-out infinite reverse',
            '&::before': {
              content: '""',
              position: 'absolute',
              bottom: -18,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 2,
              height: 28,
              background: 'linear-gradient(to bottom, rgba(236, 72, 153, 0.6), transparent)',
              borderRadius: 1,
            },
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            right: '15%',
            top: '12%',
            width: 55,
            height: 75,
            background: 'radial-gradient(ellipse at center, rgba(99, 102, 241, 0.3) 0%, transparent 70%)',
            borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
            animation: 'float 7s ease-in-out infinite',
            '&::before': {
              content: '""',
              position: 'absolute',
              bottom: -22,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 2,
              height: 32,
              background: 'linear-gradient(to bottom, rgba(99, 102, 241, 0.6), transparent)',
              borderRadius: 1,
            },
          }}
        />

        {/* Network structures - triangular clusters */}
        <Box
          sx={{
            position: 'absolute',
            left: '10%',
            bottom: '20%',
            width: 120,
            height: 100,
            '&::before': {
              content: '""',
              position: 'absolute',
              width: 6,
              height: 6,
              background: '#00f5ff',
              borderRadius: '50%',
              top: 20,
              left: 20,
              boxShadow: '0 0 20px #00f5ff',
              animation: 'pulse 2s ease-in-out infinite',
            },
            '&::after': {
              content: '""',
              position: 'absolute',
              width: 6,
              height: 6,
              background: '#ff0080',
              borderRadius: '50%',
              top: 40,
              left: 60,
              boxShadow: '0 0 20px #ff0080',
              animation: 'pulse 2.5s ease-in-out infinite',
            },
          }}
        />

        {/* Vertical glowing bars */}
        {[...Array(15)].map((_, i) => (
          <Box
            key={`bar-${i}`}
            sx={{
              position: 'absolute',
              width: 2,
              height: 20 + Math.random() * 30,
              background: i % 2 === 0 ? '#00f5ff' : '#ff0080',
              left: `${10 + Math.random() * 80}%`,
              top: `${20 + Math.random() * 60}%`,
              boxShadow: i % 2 === 0 ? '0 0 15px #00f5ff' : '0 0 15px #ff0080',
              animation: `flicker-${i} ${1 + Math.random() * 2}s ease-in-out infinite`,
              '@keyframes flicker-0': {
                '0%, 100%': { opacity: 0.3 },
                '50%': { opacity: 1 },
              },
              '@keyframes flicker-1': {
                '0%, 100%': { opacity: 0.2 },
                '50%': { opacity: 0.8 },
              },
              '@keyframes flicker-2': {
                '0%, 100%': { opacity: 0.4 },
                '50%': { opacity: 1 },
              },
              '@keyframes flicker-3': {
                '0%, 100%': { opacity: 0.3 },
                '50%': { opacity: 0.9 },
              },
              '@keyframes flicker-4': {
                '0%, 100%': { opacity: 0.2 },
                '50%': { opacity: 0.7 },
              },
              '@keyframes flicker-5': {
                '0%, 100%': { opacity: 0.4 },
                '50%': { opacity: 1 },
              },
              '@keyframes flicker-6': {
                '0%, 100%': { opacity: 0.3 },
                '50%': { opacity: 0.8 },
              },
              '@keyframes flicker-7': {
                '0%, 100%': { opacity: 0.2 },
                '50%': { opacity: 0.9 },
              },
              '@keyframes flicker-8': {
                '0%, 100%': { opacity: 0.4 },
                '50%': { opacity: 1 },
              },
              '@keyframes flicker-9': {
                '0%, 100%': { opacity: 0.3 },
                '50%': { opacity: 0.7 },
              },
              '@keyframes flicker-10': {
                '0%, 100%': { opacity: 0.2 },
                '50%': { opacity: 0.8 },
              },
              '@keyframes flicker-11': {
                '0%, 100%': { opacity: 0.4 },
                '50%': { opacity: 1 },
              },
              '@keyframes flicker-12': {
                '0%, 100%': { opacity: 0.3 },
                '50%': { opacity: 0.9 },
              },
              '@keyframes flicker-13': {
                '0%, 100%': { opacity: 0.2 },
                '50%': { opacity: 0.6 },
              },
              '@keyframes flicker-14': {
                '0%, 100%': { opacity: 0.4 },
                '50%': { opacity: 1 },
              },
            }}
          />
        ))}

        {/* Bokeh particles */}
        {[...Array(25)].map((_, i) => (
          <Box
            key={`bokeh-${i}`}
            sx={{
              position: 'absolute',
              width: 4 + Math.random() * 8,
              height: 4 + Math.random() * 8,
              borderRadius: '50%',
              background: `hsl(${200 + Math.random() * 160}, 70%, 60%)`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              filter: 'blur(1px)',
              opacity: 0.3 + Math.random() * 0.4,
              animation: `drift-${i} ${3 + Math.random() * 4}s ease-in-out infinite`,
              '@keyframes drift-0': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(10px, -10px) scale(1.2)', opacity: 0.7 },
              },
              '@keyframes drift-1': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(-8px, 12px) scale(1.1)', opacity: 0.6 },
              },
              '@keyframes drift-2': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(15px, 8px) scale(1.3)', opacity: 0.8 },
              },
              '@keyframes drift-3': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(-12px, -8px) scale(1.1)', opacity: 0.7 },
              },
              '@keyframes drift-4': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(8px, 15px) scale(1.2)', opacity: 0.5 },
              },
              '@keyframes drift-5': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(-15px, 5px) scale(1.4)', opacity: 0.9 },
              },
              '@keyframes drift-6': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(12px, -12px) scale(1.1)', opacity: 0.6 },
              },
              '@keyframes drift-7': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(-8px, 18px) scale(1.3)', opacity: 0.8 },
              },
              '@keyframes drift-8': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(18px, 3px) scale(1.2)', opacity: 0.7 },
              },
              '@keyframes drift-9': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(-5px, -15px) scale(1.1)', opacity: 0.5 },
              },
              '@keyframes drift-10': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(10px, 20px) scale(1.3)', opacity: 0.6 },
              },
              '@keyframes drift-11': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(-20px, 8px) scale(1.2)', opacity: 0.8 },
              },
              '@keyframes drift-12': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(15px, -5px) scale(1.1)', opacity: 0.7 },
              },
              '@keyframes drift-13': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(-12px, 22px) scale(1.4)', opacity: 0.9 },
              },
              '@keyframes drift-14': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(22px, 12px) scale(1.3)', opacity: 0.6 },
              },
              '@keyframes drift-15': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(-18px, -3px) scale(1.1)', opacity: 0.5 },
              },
              '@keyframes drift-16': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(5px, 25px) scale(1.2)', opacity: 0.8 },
              },
              '@keyframes drift-17': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(-25px, 15px) scale(1.4)', opacity: 0.7 },
              },
              '@keyframes drift-18': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(20px, -8px) scale(1.1)', opacity: 0.6 },
              },
              '@keyframes drift-19': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(-15px, 28px) scale(1.3)', opacity: 0.9 },
              },
              '@keyframes drift-20': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(25px, 5px) scale(1.2)', opacity: 0.8 },
              },
              '@keyframes drift-21': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(-8px, -20px) scale(1.1)', opacity: 0.5 },
              },
              '@keyframes drift-22': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.2 },
                '50%': { transform: 'translate(12px, 30px) scale(1.4)', opacity: 0.7 },
              },
              '@keyframes drift-23': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.4 },
                '50%': { transform: 'translate(-30px, 10px) scale(1.3)', opacity: 0.6 },
              },
              '@keyframes drift-24': {
                '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: 0.3 },
                '50%': { transform: 'translate(18px, -12px) scale(1.1)', opacity: 0.8 },
              },
            }}
          />
        ))}
      </Box>
    </Box>
  );
}

export default Login;



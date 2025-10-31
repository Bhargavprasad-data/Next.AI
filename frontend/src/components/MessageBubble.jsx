import React, { useState } from 'react';
import { Box, Typography, Avatar, IconButton, Tooltip, TextField, CircularProgress } from '@mui/material';
import { SmartToy as BotIcon, Person as PersonIcon, ContentCopy as CopyIcon, Edit as EditIcon, Check as CheckIcon, Close as CloseIcon, AttachFile as AttachFileIcon, Image as ImageIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

function MessageBubble({ message, onEditMessage, isProcessingEdit = false }) {
  const isUser = message.role === 'user';
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  const [showActions, setShowActions] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleEdit = () => {
    console.log('Edit button clicked for message:', message.content);
    setIsEditing(true);
    setEditText(message.content);
  };

  const handleSaveEdit = () => {
    console.log('Save edit clicked, new content:', editText.trim());
    if (onEditMessage) {
      onEditMessage(message, editText.trim());
    }
    setIsEditing(false);
    // Optionally signal parent to clear editingMessageId if needed (parent clean-up)
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditText(message.content);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        py: 2,
        px: 3,
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        '&:hover': {
          bgcolor: isUser ? 'transparent' : 'rgba(255, 255, 255, 0.02)',
        },
        transition: 'background-color 0.2s',
      }}
    >
      {!isUser && (
        <Box sx={{ flexShrink: 0 }}>
          <Avatar sx={{ bgcolor: '#6A6ADF', width: 32, height: 32 }}>
            <BotIcon sx={{ fontSize: 20 }} />
          </Avatar>
        </Box>
      )}

      {/* Message Content */}
      <Box
        sx={{
          maxWidth: '80%',
          background: isUser ? 'linear-gradient(to right, #6A6ADF, #8A6AE0)' : 'transparent',
          color: 'white',
          borderRadius: isUser ? '18px 18px 4px 18px' : 'none',
          px: 2,
          py: 1.5,
          wordBreak: 'break-word',
          position: 'relative',
          '&:hover .message-actions': {
            opacity: 1,
          },
        }}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {isUser ? (
          <>
            {isEditing ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <TextField
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  multiline
                  variant="outlined"
                  size="small"
                  autoFocus
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                      bgcolor: 'rgba(255, 255, 255, 0.15)',
                      borderRadius: 2,
                      '& fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderRadius: 2,
                      },
                      '&:hover fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.5)',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.8)',
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                  }}
                />
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                  <IconButton
                    size="small"
                    onClick={handleSaveEdit}
                    disabled={isProcessingEdit}
                    sx={{ 
                      color: 'white', 
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      width: 32,
                      height: 32,
                      '&:hover': {
                        bgcolor: 'rgba(255, 255, 255, 0.3)',
                      },
                      '&:disabled': {
                        bgcolor: 'rgba(255, 255, 255, 0.1)',
                        color: 'rgba(255, 255, 255, 0.5)',
                      },
                    }}
                  >
                    {isProcessingEdit ? (
                      <CircularProgress size={16} sx={{ color: 'white' }} />
                    ) : (
                      <CheckIcon fontSize="small" />
                    )}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={handleCancelEdit}
                    sx={{ 
                      color: 'white', 
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      width: 32,
                      height: 32,
                      '&:hover': {
                        bgcolor: 'rgba(255, 255, 255, 0.3)',
                      },
                    }}
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            ) : (
              <>
                <Typography
                  variant="body1"
                  sx={{
                    lineHeight: 1.75,
                  }}
                >
                  {message.content}
                </Typography>
                
                {/* File Attachments */}
                {message.files && message.files.length > 0 && (
                  <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {message.files.map((file, index) => (
                      <Box
                        key={index}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          bgcolor: 'rgba(255, 255, 255, 0.1)',
                          px: 1.5,
                          py: 0.5,
                          borderRadius: 1,
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                        }}
                      >
                        {file.type && file.type.startsWith('image/') ? (
                          <ImageIcon sx={{ color: 'white', fontSize: 16 }} />
                        ) : (
                          <AttachFileIcon sx={{ color: 'white', fontSize: 16 }} />
                        )}
                        <Typography variant="caption" sx={{ color: 'white' }}>
                          {file.name}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}
                
                {/* Action Buttons */}
                <Box
                  className="message-actions"
                  sx={{
                    position: 'absolute',
                    top: -8,
                    right: -8,
                    display: 'flex',
                    gap: 0.5,
                    opacity: showActions ? 1 : 0,
                    transition: 'opacity 0.2s',
                    bgcolor: 'rgba(0, 0, 0, 0.7)',
                    borderRadius: 1,
                    p: 0.5,
                  }}
                >
                  <Tooltip title="Copy">
                    <IconButton
                      size="small"
                      onClick={handleCopy}
                      sx={{ color: 'white' }}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Edit">
                    <IconButton
                      size="small"
                      onClick={handleEdit}
                      sx={{ color: 'white' }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </>
            )}
          </>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => (
                <Typography
                  variant="body1"
                  sx={{
                    mb: 2,
                    wordBreak: 'break-word',
                    lineHeight: 1.75,
                  }}
                >
                  {children}
                </Typography>
              ),
              code: ({ children }) => (
                <Box
                  component="code"
                  sx={{
                    bgcolor: '#40414f',
                    color: '#d1d1d1',
                    px: 0.75,
                    py: 0.25,
                    borderRadius: 0.5,
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                  }}
                >
                  {children}
                </Box>
              ),
              pre: ({ children }) => (
                <Box
                  component="pre"
                  sx={{
                    bgcolor: '#40414f',
                    p: 2,
                    borderRadius: 1,
                    overflowX: 'auto',
                    mb: 2,
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    border: '1px solid #565869',
                  }}
                >
                  {children}
                </Box>
              ),
              h1: ({ children }) => (
                <Typography variant="h4" sx={{ mb: 2, mt: 1, fontWeight: 700 }}>
                  {children}
                </Typography>
              ),
              h2: ({ children }) => (
                <Typography variant="h5" sx={{ mb: 2, mt: 1, fontWeight: 600 }}>
                  {children}
                </Typography>
              ),
              h3: ({ children }) => (
                <Typography variant="h6" sx={{ mb: 1, mt: 1 }}>
                  {children}
                </Typography>
              ),
              ul: ({ children }) => (
                <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              ol: ({ children }) => (
                <Box component="ol" sx={{ pl: 2, mb: 2 }}>
                  {children}
                </Box>
              ),
              li: ({ children }) => (
                <Box component="li" sx={{ mb: 0.5 }}>
                  {children}
                </Box>
              ),
              strong: ({ children }) => (
                <Box component="strong" sx={{ fontWeight: 700 }}>
                  {children}
                </Box>
              ),
              em: ({ children }) => (
                <Box component="em" sx={{ fontStyle: 'italic' }}>
                  {children}
                </Box>
              ),
              blockquote: ({ children }) => (
                <Box
                  component="blockquote"
                  sx={{
                    borderLeft: '4px solid #10a37f',
                    pl: 2,
                    mb: 2,
                    fontStyle: 'italic',
                    color: '#8e8ea0',
                  }}
                >
                  {children}
                </Box>
              ),
              a: ({ children, href }) => (
                <Box
                  component="a"
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    color: '#10a37f',
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  {children}
                </Box>
              ),
              table: ({ children }) => (
                <Box
                  component="table"
                  sx={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    mb: 2,
                    backgroundColor: 'rgba(255,255,255,0.04)',
                    borderRadius: 1,
                    overflow: 'hidden',
                  }}
                >
                  {children}
                </Box>
              ),
              thead: ({ children }) => (
                <Box component="thead" sx={{ backgroundColor: 'rgba(106,106,223,0.14)' }}>
                  {children}
                </Box>
              ),
              tbody: ({ children }) => <Box component="tbody">{children}</Box>,
              tr: ({ children }) => (
                <Box
                  component="tr"
                  sx={{
                    borderBottom: '1px solid #555',
                    '&:last-child': {
                      borderBottom: 'none',
                    },
                  }}
                >
                  {children}
                </Box>
              ),
              th: ({ children }) => (
                <Box
                  component="th"
                  sx={{
                    p: 1.2,
                    border: '1px solid #6167a1',
                    backgroundColor: 'rgba(106,106,223,0.15)',
                    color: '#fafaff',
                    fontWeight: 700,
                    textAlign: 'left',
                    fontSize: '1rem',
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#fafaff', fontSize: 'inherit' }}>{children}</Typography>
                </Box>
              ),
              td: ({ children }) => (
                <Box
                  component="td"
                  sx={{
                    p: 1.2,
                    border: '1px solid #444',
                    color: '#fff',
                    fontSize: '0.98rem',
                  }}
                >
                  <Typography variant="body2" sx={{ color: '#fff', fontSize: 'inherit' }}>{children}</Typography>
                </Box>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </Box>

      {isUser && (
        <Box sx={{ flexShrink: 0 }}>
          <Avatar sx={{ bgcolor: '#6A6ADF', width: 32, height: 32 }}>
            <PersonIcon sx={{ fontSize: 20 }} />
          </Avatar>
        </Box>
      )}
    </Box>
  );
}

export default MessageBubble;

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  List,
  ListItemButton,
  ListItemText,
  Drawer,
  Avatar,
  Menu,
  MenuItem,
  CircularProgress,
  Grow,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Logout,
  SmartToy,
  Edit as EditIcon,
  LibraryBooks as LibraryIcon,
  Folder as FolderIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  AttachFile as AttachFileIcon,
  Image as ImageIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { chatService } from '../services/api';
import MessageBubble from './MessageBubble';
import RobotIcon from './RobotIcon';

function ChatInterface({ user, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const data = await chatService.getHistory();
      const allMessages = data.messages || [];
      
      // Group messages by conversation_id
      const conversationsMap = new Map();
      
      allMessages.forEach((msg) => {
        // Use conversation_id if available
        const convoId = msg.conversation_id;
        
        if (convoId) {
          if (!conversationsMap.has(convoId)) {
            conversationsMap.set(convoId, {
              id: convoId,
              messages: [],
              title: '',
              lastMessageTime: new Date(msg.created_at || Date.now()),
            });
          }
          
          const conversation = conversationsMap.get(convoId);
          conversation.messages.push(msg);
          
          // Update last message time
          const msgTime = new Date(msg.created_at || Date.now());
          if (msgTime > conversation.lastMessageTime) {
            conversation.lastMessageTime = msgTime;
          }
          
          // Set title from first user message (only if not already set)
          if (msg.role === 'user' && !conversation.title) {
            conversation.title = msg.content.length > 35 
              ? msg.content.substring(0, 35) + '...' 
              : msg.content;
          }
        }
      });
      
      // Sort messages within each conversation by creation time
      conversationsMap.forEach((conversation) => {
        conversation.messages.sort((a, b) => 
          new Date(a.created_at || 0) - new Date(b.created_at || 0)
        );
      });
      
      // Convert map to array and sort by newest conversation first
      const conversationsArray = Array.from(conversationsMap.values())
        .sort((a, b) => b.lastMessageTime - a.lastMessageTime);
      
      console.log('Loaded conversations:', conversationsArray.length);
      setConversations(conversationsArray);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    const newUserMessage = {
      content: userMessage,
      role: 'user',
      created_at: new Date(),
    };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const response = await chatService.sendMessage(userMessage, currentConversationId);
      
      const newAssistantMessage = {
        content: response.response,
        role: 'assistant',
        created_at: new Date(),
      };
      setMessages((prev) => [...prev, newAssistantMessage]);
      
      // Update current conversation ID if we got a new one
      if (response.context_id && !currentConversationId) {
        setCurrentConversationId(response.context_id);
      }
      
      // Refresh conversations to show the updated chat
      setTimeout(async () => {
        await loadConversations();
      }, 1000); // Increased delay to ensure backend has processed the message
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        created_at: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    onLogout();
  };

  const handleNewChat = async () => {
    // Save current conversation if it has messages
    if (messages.length > 0 && currentConversationId) {
      try {
        // Get the first user message as title
        const firstUserMessage = messages.find(msg => msg.role === 'user');
        const title = firstUserMessage ? 
          (firstUserMessage.content.length > 35 ? 
            firstUserMessage.content.substring(0, 35) + '...' : 
            firstUserMessage.content) : 
          'New Conversation';
        
        // Explicitly save the conversation
        await chatService.saveConversation(currentConversationId, title);
        
        // Refresh conversations to show the saved chat
        await loadConversations();
      } catch (error) {
        console.error('Error saving conversation:', error);
      }
    }
    
    // Clear current chat
    setMessages([]);
    setInput('');
    setCurrentConversationId(null);
  };

  const handleLoadConversation = (conversation) => {
    setMessages(conversation.messages);
    setCurrentConversationId(conversation.id);
    setSidebarOpen(false); // Close sidebar on mobile after selecting conversation
    
    // Scroll to top to show the loaded conversation
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  const handleEditMessage = async (message, newContent) => {
    console.log('handleEditMessage called with:', { message, newContent });
    try {
      // Set editing state for this message
      setEditingMessageId(message.created_at || message.id);
      
      // Update the message in the local state
      setMessages(prev => 
        prev.map(msg => 
          msg === message ? { ...msg, content: newContent } : msg
        )
      );
      
      // If this is a user message, treat the edit as a new input and get AI response
      if (message.role === 'user') {
        setLoading(true);
        
        try {
          // Find the index of the current user message
          const messageIndex = messages.findIndex(msg => msg === message);
          
          // Remove all messages after the edited user message (including old AI responses)
          setMessages(prev => prev.slice(0, messageIndex + 1));
          
          // Send the edited message as a new input
          const response = await chatService.sendMessage(newContent, currentConversationId);
          
          // Add the new AI response to messages
          const aiMessage = {
            role: 'assistant',
            content: response.response,
            created_at: new Date().toISOString(),
            conversation_id: response.context_id
          };
          
          setMessages(prev => [...prev, aiMessage]);
          setCurrentConversationId(response.context_id);
          
          // Scroll to bottom to show the new response
          setTimeout(() => {
            if (messagesEndRef.current) {
              messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
            }
          }, 100);
          
          // Refresh conversations
          await loadConversations();
          
        } catch (error) {
          console.error('Error getting AI response for edited message:', error);
          // Show error message
          const errorMessage = {
            role: 'assistant',
            content: 'Sorry, I encountered an error processing your edited message. Please try again.',
            created_at: new Date().toISOString(),
            conversation_id: currentConversationId
          };
          setMessages(prev => [...prev, errorMessage]);
        } finally {
          setLoading(false);
          setEditingMessageId(null);
        }
      } else {
        // For non-user messages, just clear the editing state
        setEditingMessageId(null);
      }
      
      // Refresh conversations to reflect the change
      await loadConversations();
    } catch (error) {
      console.error('Error editing message:', error);
      setEditingMessageId(null);
    }
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsUploading(true);
    
    try {
      const uploadPromises = files.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await chatService.uploadFile(formData);
        return {
          id: response.file_id,
          name: file.name,
          type: file.type,
          size: file.size,
          url: response.url,
          content: response.content || '',
        };
      });

      const uploadedFiles = await Promise.all(uploadPromises);
      setUploadedFiles(prev => [...prev, ...uploadedFiles]);
      
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const removeUploadedFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleSendWithFiles = async (e) => {
    e.preventDefault();
    if ((!input.trim() && uploadedFiles.length === 0) || loading || isUploading) return;

    const userMessage = input.trim();
    const fileInfo = uploadedFiles.map(file => ({
      id: file.id,
      name: file.name,
      type: file.type,
      content: file.content,
    }));

    setInput('');
    setLoading(true);

    const newUserMessage = {
      content: userMessage,
      role: 'user',
      created_at: new Date(),
      files: fileInfo,
    };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const response = await chatService.sendMessageWithFiles(userMessage, fileInfo, currentConversationId);
      
      const newAssistantMessage = {
        content: response.response,
        role: 'assistant',
        created_at: new Date(),
      };
      setMessages((prev) => [...prev, newAssistantMessage]);
      
      // Update current conversation ID if we got a new one
      if (response.context_id && !currentConversationId) {
        setCurrentConversationId(response.context_id);
      }
      
      // Clear uploaded files
      setUploadedFiles([]);
      
      // Refresh conversations to show the updated chat
      setTimeout(async () => {
        await loadConversations();
      }, 1000);
    } catch (error) {
      console.error('Error sending message with files:', error);
      const errorMessage = {
        content: 'Sorry, I encountered an error processing your files. Please try again.',
        role: 'assistant',
        created_at: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const drawerWidth = sidebarOpen ? 280 : 0;

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#343541' }}>
      {/* Sidebar */}
      <Drawer
        variant="persistent"
        open={sidebarOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            bgcolor: '#202123',
            border: 'none',
          },
        }}
      >
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
          {/* App Logo */}
          <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: 2 }}>
            <Box
              sx={{
                width: 60,
                height: 60,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #8B7CB8 0%, #9D8BBE 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 16px rgba(139, 124, 184, 0.4)',
                flexShrink: 0,
              }}
            >
              <RobotIcon size={50} color="white" />
            </Box>
            <Typography
              sx={{
                fontSize: '24px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #8B7CB8 0%, #9D8BBE 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '0.5px',
              }}
            >
              Next.AI
            </Typography>
          </Box>

          {/* New Chat Button */}
          <Box
            onClick={handleNewChat}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              p: 2,
              borderRadius: 2,
              bgcolor: '#343541',
              cursor: 'pointer',
              mb: 3,
              transition: 'all 0.2s ease',
              '&:hover': {
                bgcolor: '#40414f',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
              },
            }}
          >
            <EditIcon sx={{ color: 'white', fontSize: 20 }} />
            <Typography sx={{ color: 'white', fontWeight: 500 }}>
              New chat
            </Typography>
          </Box>

          {/* Navigation Items */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 4 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 1.5,
                borderRadius: 1,
                cursor: 'pointer',
                transition: 'background-color 0.2s ease',
                '&:hover': { bgcolor: '#343541' },
              }}
            >
              <LibraryIcon sx={{ color: 'white', fontSize: 20 }} />
              <Typography sx={{ color: 'white', fontSize: '0.9rem' }}>
                Library
              </Typography>
            </Box>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 1.5,
                borderRadius: 1,
                cursor: 'pointer',
                transition: 'background-color 0.2s ease',
                '&:hover': { bgcolor: '#343541' },
              }}
            >
              <FolderIcon sx={{ color: 'white', fontSize: 20 }} />
              <Typography sx={{ color: 'white', fontSize: '0.9rem' }}>
                Projects
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ bgcolor: '#40414f', mb: 2 }} />

          {/* Chat History */}
          <Typography
            variant="body2"
            sx={{ 
              px: 1, 
              py: 1, 
              color: '#8e8ea0', 
              fontWeight: 600,
              fontSize: '0.8rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            CHATS
          </Typography>
          
          <Box
            sx={{
              flexGrow: 1,
              overflow: 'auto',
              mt: 1,
            }}
          >
            {conversations
              .slice(0, 20)
              .map((conversation, index) => (
                <Box
                  key={conversation.id || index}
                  onClick={() => handleLoadConversation(conversation)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    p: 1.5,
                    borderRadius: 1,
                    mb: 0.5,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s ease',
                    bgcolor: currentConversationId === conversation.id ? '#343541' : 'transparent',
                    '&:hover': { bgcolor: '#343541' },
                  }}
                >
                  <Typography
                    sx={{ 
                      color: 'white',
                      fontSize: '0.9rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1,
                    }}
                  >
                    {conversation.title}
                  </Typography>
                </Box>
              ))}
          </Box>

          {/* Logout Button */}
          {/* <Box
            onClick={handleLogout}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              p: 2,
              borderRadius: 2,
              bgcolor: '#363636',
              cursor: 'pointer',
              mb: 2,
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              '&:hover': {
                bgcolor: '#404040',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              },
            }}
          >
            <Logout sx={{ color: 'white', fontSize: 20 }} />
            <Typography sx={{ color: 'white', fontWeight: 500 }}>
              Logout
            </Typography>
          </Box> */}

          {/* User Profile */}
          <Box
            sx={{
              p: 2,
              borderTop: '1px solid #40414f',
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
            }}
          >
            <Avatar
              sx={{
                bgcolor: 'linear-gradient(to right, #6A6ADF, #8A6AE0)',
                width: 32,
                height: 32,
                fontSize: '0.875rem',
              }}
            >
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" sx={{ color: 'white', fontWeight: 500, fontSize: '0.9rem' }}>
                {user?.username || 'User'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#8e8ea0', fontSize: '0.75rem' }}>
                Free
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{
                color: 'white',
                '&:hover': { bgcolor: '#40414f' },
              }}
            >
              <SettingsIcon fontSize="small" />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleLogout}>
                <Logout sx={{ mr: 1 }} />
                Logout
              </MenuItem>
            </Menu>
          </Box>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: '#343541',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            px: 2,
            py: 1.5,
            bgcolor: '#40414f',
            borderBottom: '1px solid #565869',
          }}
        >
          <IconButton
            onClick={() => setSidebarOpen(!sidebarOpen)}
            sx={{ color: 'white', mr: 1 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ color: 'white', flexGrow: 1 }}>
            Chat with Next.AI
          </Typography>
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flexGrow: 1,
            overflowY: 'auto',
            px: 2,
            py: 4,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {messages.length === 0 && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: '#8e8ea0',
              }}
            >
              <SmartToy sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
              <Typography variant="h5" sx={{ mb: 1, color: 'white' }}>
                How can I help you today?
              </Typography>
              <Typography variant="body1" sx={{ color: '#8e8ea0' }}>
                Start a new conversation by typing a message below
              </Typography>
            </Box>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              onEditMessage={handleEditMessage}
              isProcessingEdit={editingMessageId === (message.created_at || message.id)}
            />
          ))}

          {loading && (
            <Grow in={loading}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  p: 2,
                  borderRadius: 2,
                  background: 'rgba(102, 126, 234, 0.1)',
                }}
              >
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ color: '#8e8ea0' }}>
                  Next.AI is thinking...
                </Typography>
              </Box>
            </Grow>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box
          component="form"
          onSubmit={handleSendWithFiles}
          sx={{
            p: 3,
            bgcolor: '#40414f',
            borderTop: '1px solid #565869',
          }}
        >
          {/* Uploaded Files Preview */}
          {uploadedFiles.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ color: '#8e8ea0', mb: 1 }}>
                Uploaded Files:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {uploadedFiles.map((file) => (
                  <Box
                    key={file.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      bgcolor: 'rgba(255, 255, 255, 0.1)',
                      px: 2,
                      py: 1,
                      borderRadius: 1,
                      border: '1px solid #565869',
                    }}
                  >
                    {file.type.startsWith('image/') ? (
                      <ImageIcon sx={{ color: '#6A6ADF', fontSize: 20 }} />
                    ) : (
                      <AttachFileIcon sx={{ color: '#6A6ADF', fontSize: 20 }} />
                    )}
                    <Typography variant="body2" sx={{ color: 'white', maxWidth: 200 }}>
                      {file.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={() => removeUploadedFile(file.id)}
                      sx={{ color: '#8e8ea0' }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            {/* File Upload Button */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              multiple
              accept=".txt,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.csv,.xlsx,.xls"
              style={{ display: 'none' }}
            />
            <IconButton
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || isUploading}
              sx={{
                color: '#8e8ea0',
                '&:hover': { color: '#6A6ADF' },
                '&:disabled': { color: 'rgba(255, 255, 255, 0.3)' },
              }}
            >
              <AttachFileIcon />
            </IconButton>

            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Ask Next.AI... (or upload files)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendWithFiles(e);
                }
              }}
              variant="outlined"
              disabled={loading || isUploading}
              sx={{
                bgcolor: '#40414f',
                '& .MuiOutlinedInput-root': {
                  bgcolor: '#40414f',
                  color: 'white',
                  '& fieldset': {
                    borderColor: '#565869',
                  },
                  '&:hover fieldset': {
                    borderColor: '#8e8ea0',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#6A6ADF',
                  },
                },
                '& .MuiInputBase-input::placeholder': {
                  color: '#8e8ea0',
                },
              }}
            />
            <IconButton
              type="submit"
              color="primary"
              disabled={loading || isUploading || (!input.trim() && uploadedFiles.length === 0)}
              sx={{
                bgcolor: '#6A6ADF',
                color: 'white',
                '&:hover': { bgcolor: '#5A5ADF' },
                '&:disabled': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {isUploading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            </IconButton>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default ChatInterface;

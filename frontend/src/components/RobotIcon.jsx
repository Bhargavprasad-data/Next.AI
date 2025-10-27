import React from 'react';
import { Box } from '@mui/material';

const RobotIcon = ({ size = 50, color = 'white' }) => {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Brain outline - smooth oval shape without prominent indentations */}
        <path
          d="M50 12C42 12 36 16 36 22C36 28 39 32 42 34C45 36 47 38 46 40C45 42 44 45 44 47C44 49 46 50 48 50C50 50 52 49 52 47C52 45 51 42 50 40C49 38 51 36 54 34C57 32 60 28 60 22C60 16 54 12 50 12Z"
          fill={color}
        />
        
        {/* Central vertical division line */}
        <line
          x1="50"
          y1="18"
          x2="50"
          y2="78"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
        />
        
        {/* Left hemisphere - 5 dots with connecting lines */}
        
        {/* Top larger dot */}
        <circle cx="42" cy="28" r="2.5" fill={color} />
        
        {/* Middle three smaller dots */}
        <circle cx="40" cy="38" r="1.8" fill={color} />
        <circle cx="42" cy="45" r="1.8" fill={color} />
        <circle cx="40" cy="52" r="1.8" fill={color} />
        
        {/* Bottom larger dot */}
        <circle cx="43" cy="62" r="2.5" fill={color} />
        
        {/* Connecting lines in left hemisphere */}
        <line x1="42" y1="28" x2="40" y2="38" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="40" y1="38" x2="42" y2="45" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="42" y1="45" x2="40" y2="52" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="40" y1="52" x2="43" y2="62" stroke={color} strokeWidth="2" strokeLinecap="round" />
        
        {/* Right hemisphere - 5 dots with connecting lines */}
        
        {/* Top larger dot */}
        <circle cx="58" cy="28" r="2.5" fill={color} />
        
        {/* Middle three smaller dots */}
        <circle cx="60" cy="38" r="1.8" fill={color} />
        <circle cx="58" cy="45" r="1.8" fill={color} />
        <circle cx="60" cy="52" r="1.8" fill={color} />
        
        {/* Bottom larger dot */}
        <circle cx="57" cy="62" r="2.5" fill={color} />
        
        {/* Connecting lines in right hemisphere */}
        <line x1="58" y1="28" x2="60" y2="38" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="60" y1="38" x2="58" y2="45" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="58" y1="45" x2="60" y2="52" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <line x1="60" y1="52" x2="57" y2="62" stroke={color} strokeWidth="2" strokeLinecap="round" />
      </svg>
    </Box>
  );
};

export default RobotIcon;

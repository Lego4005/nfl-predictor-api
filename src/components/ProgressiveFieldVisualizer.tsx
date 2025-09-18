/**
 * Progressive Field Visualizer for mobile devices
 * Responsive football field with game state visualization
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GameUpdate } from '../services/websocketService';

interface ProgressiveFieldVisualizerProps {
  gameData?: GameUpdate;
  gameId: string;
  mobileOptimized?: boolean;
  className?: string;
}

interface FieldPosition {
  yardLine: number;
  side: 'home' | 'away'; // Which team's side of the field
}

const ProgressiveFieldVisualizer: React.FC<ProgressiveFieldVisualizerProps> = ({
  gameData,
  gameId,
  mobileOptimized = false,
  className = ''
}) => {
  // Calculate field dimensions based on mobile optimization
  const fieldDimensions = useMemo(() => {
    const aspectRatio = 2.5; // Football field is roughly 2.5:1
    const maxWidth = mobileOptimized ? 340 : 600;
    const width = Math.min(maxWidth, window.innerWidth - 32);
    const height = width / aspectRatio;

    return { width, height };
  }, [mobileOptimized]);

  // Parse ball position from game data
  const ballPosition = useMemo((): FieldPosition => {
    if (!gameData?.possession_team || !gameData?.yard_line) {
      return { yardLine: 50, side: 'home' };
    }

    // Parse yard line (e.g., "NYG 25" means 25 yards from Giants' goal line)
    const parts = gameData.yard_line.split(' ');
    const yardLine = parseInt(parts[1]) || 50;
    const team = parts[0];

    // Determine which side of field
    const side = team === gameData.home_team ? 'home' : 'away';

    return { yardLine, side };
  }, [gameData]);

  // Calculate ball position on SVG field (0-100 scale)
  const ballPositionPercent = useMemo(() => {
    const { yardLine, side } = ballPosition;

    if (side === 'home') {
      // Home team's side: 0-50 yard line maps to 0-50%
      return (50 - yardLine) + 50;
    } else {
      // Away team's side: 0-50 yard line maps to 50-100%
      return yardLine;
    }
  }, [ballPosition]);

  // Generate yard line markers
  const yardLines = useMemo(() => {
    const lines = [];
    for (let yard = 10; yard <= 90; yard += 10) {
      const xPercent = yard;
      const isGoalLine = yard === 10 || yard === 90;
      const is50YardLine = yard === 50;

      lines.push({
        yard,
        xPercent,
        isGoalLine,
        is50YardLine,
        label: is50YardLine ? '50' : Math.min(yard, 100 - yard).toString()
      });
    }
    return lines;
  }, []);

  // Generate hash marks
  const hashMarks = useMemo(() => {
    const marks = [];
    for (let yard = 5; yard <= 95; yard += 5) {
      if (yard % 10 !== 0) { // Skip main yard lines
        marks.push({
          yard,
          xPercent: yard
        });
      }
    }
    return marks;
  }, []);

  // Down and distance info
  const downInfo = useMemo(() => {
    if (!gameData?.down || !gameData?.distance) return null;

    const downText = ['1st', '2nd', '3rd', '4th'][gameData.down - 1] || `${gameData.down}th`;
    const distanceText = gameData.distance === 1 ? 'Goal' : `& ${gameData.distance}`;

    return `${downText} ${distanceText}`;
  }, [gameData]);

  // Field colors based on team
  const fieldColors = useMemo(() => {
    const homeColor = '#1f2937'; // Dark gray
    const awayColor = '#374151'; // Lighter gray
    const goalLineColor = '#ef4444'; // Red

    return { homeColor, awayColor, goalLineColor };
  }, []);

  if (!gameData) {
    return (
      <div className={`progressive-field-empty ${className} flex items-center justify-center p-8`}>
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">🏈</div>
          <div className="text-sm">No game data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`progressive-field-visualizer ${className} space-y-4`}>
      {/* Game status header */}
      <div className="flex justify-between items-center text-sm">
        <div className="font-medium">
          {gameData.quarter ? `Q${gameData.quarter}` : 'Game'}
          {gameData.time_remaining && ` • ${gameData.time_remaining}`}
        </div>
        <div className="text-right">
          {downInfo && (
            <div className="font-medium text-blue-400">{downInfo}</div>
          )}
          {gameData.possession_team && (
            <div className="text-xs text-gray-400">
              {gameData.possession_team} Ball
            </div>
          )}
        </div>
      </div>

      {/* Field visualization */}
      <div className="relative bg-green-800 rounded-lg overflow-hidden">
        <svg
          width="100%"
          height={fieldDimensions.height}
          viewBox="0 0 100 40"
          className="block"
        >
          {/* Field background */}
          <rect
            x="0"
            y="0"
            width="100"
            height="40"
            fill="url(#fieldGradient)"
          />

          {/* Define gradients */}
          <defs>
            <linearGradient id="fieldGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={fieldColors.awayColor} />
              <stop offset="50%" stopColor="#059669" />
              <stop offset="100%" stopColor={fieldColors.homeColor} />
            </linearGradient>

            <filter id="ballShadow">
              <feDropShadow dx="1" dy="1" stdDeviation="1" floodOpacity="0.3"/>
            </filter>
          </defs>

          {/* Goal lines */}
          <line x1="10" y1="5" x2="10" y2="35" stroke={fieldColors.goalLineColor} strokeWidth="0.5" />
          <line x1="90" y1="5" x2="90" y2="35" stroke={fieldColors.goalLineColor} strokeWidth="0.5" />

          {/* End zones */}
          <rect x="0" y="5" width="10" height="30" fill="rgba(239, 68, 68, 0.1)" />
          <rect x="90" y="5" width="10" height="30" fill="rgba(239, 68, 68, 0.1)" />

          {/* Yard lines */}
          {yardLines.map((line) => (
            <g key={line.yard}>
              <line
                x1={line.xPercent}
                y1="5"
                x2={line.xPercent}
                y2="35"
                stroke="white"
                strokeWidth={line.is50YardLine ? "0.3" : "0.2"}
                opacity={line.is50YardLine ? "1" : "0.6"}
              />
              {/* Yard numbers */}
              <text
                x={line.xPercent}
                y="12"
                fill="white"
                fontSize="3"
                textAnchor="middle"
                opacity="0.8"
              >
                {line.label}
              </text>
              <text
                x={line.xPercent}
                y="32"
                fill="white"
                fontSize="3"
                textAnchor="middle"
                opacity="0.8"
                transform={`rotate(180 ${line.xPercent} 32)`}
              >
                {line.label}
              </text>
            </g>
          ))}

          {/* Hash marks */}
          {hashMarks.map((mark) => (
            <g key={mark.yard}>
              <line
                x1={mark.xPercent}
                y1="10"
                x2={mark.xPercent}
                y2="12"
                stroke="white"
                strokeWidth="0.1"
                opacity="0.6"
              />
              <line
                x1={mark.xPercent}
                y1="28"
                x2={mark.xPercent}
                y2="30"
                stroke="white"
                strokeWidth="0.1"
                opacity="0.6"
              />
            </g>
          ))}

          {/* 50-yard line special styling */}
          <text
            x="50"
            y="22"
            fill="white"
            fontSize="6"
            textAnchor="middle"
            fontWeight="bold"
            opacity="0.3"
          >
            50
          </text>

          {/* Ball position */}
          <AnimatePresence>
            <motion.circle
              cx={ballPositionPercent}
              cy="20"
              r="1.5"
              fill="#8B4513"
              stroke="white"
              strokeWidth="0.2"
              filter="url(#ballShadow)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 20
              }}
            />
          </AnimatePresence>

          {/* First down marker (if available) */}
          {gameData.distance && gameData.distance < 50 && (
            <motion.line
              x1={(ballPositionPercent + (gameData.distance / 100 * 90)) % 100}
              y1="5"
              x2={(ballPositionPercent + (gameData.distance / 100 * 90)) % 100}
              y2="35"
              stroke="#fbbf24"
              strokeWidth="0.3"
              strokeDasharray="1,1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.8 }}
              transition={{ delay: 0.3 }}
            />
          )}

          {/* Team name labels */}
          <text
            x="5"
            y="38"
            fill="white"
            fontSize="2.5"
            textAnchor="middle"
            opacity="0.8"
          >
            {gameData.away_team}
          </text>
          <text
            x="95"
            y="38"
            fill="white"
            fontSize="2.5"
            textAnchor="middle"
            opacity="0.8"
          >
            {gameData.home_team}
          </text>
        </svg>

        {/* Overlay information */}
        {gameData.play_description && (
          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white p-2">
            <div className="text-xs text-center truncate">
              {gameData.play_description}
            </div>
          </div>
        )}
      </div>

      {/* Field legend for mobile */}
      {mobileOptimized && (
        <div className="flex justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
            <span>1st Down</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-800 rounded-full"></div>
            <span>Ball</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-1 bg-red-500"></div>
            <span>Goal Line</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressiveFieldVisualizer;
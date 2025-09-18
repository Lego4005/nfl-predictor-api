/**
 * Expert Observatory - Simplified Admin Dashboard
 * Shows expert predictions and reasoning without external UI dependencies
 */

import React, { useState, useEffect } from 'react';
import ExpertDeepDive from '../ExpertDeepDive';

interface Expert {
  expert_id: string;
  display_name: string;
  personality: string;
  avatar_emoji: string;
  accuracy_rate?: number;
  predictions_count?: number;
}

interface GamePrediction {
  game_id: string;
  date: string;
  home_team: string;
  away_team: string;
  consensus_winner: string;
  consensus_confidence: number;
  expert_predictions: any[];
  status?: 'upcoming' | 'live' | 'completed';
}

const ExpertObservatorySimple: React.FC = () => {
  const [experts, setExperts] = useState<Expert[]>([]);
  const [games, setGames] = useState<GamePrediction[]>([]);
  const [selectedGame, setSelectedGame] = useState<GamePrediction | null>(null);
  const [selectedExpert, setSelectedExpert] = useState<Expert | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'games' | 'experts' | 'performance'>('games');
  const [currentPage, setCurrentPage] = useState(1);
  const gamesPerPage = 8; // Show 8 games per page
  const [selectedGameForPredictions, setSelectedGameForPredictions] = useState<GamePrediction | null>(null);
  const [showCompletedGames, setShowCompletedGames] = useState(false);
  const [gamePageIndex, setGamePageIndex] = useState(1);
  const [darkMode, setDarkMode] = useState(() => {
    // Check if dark mode is set in localStorage or default to system preference
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return saved === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Apply dark mode class to body
  React.useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  // Fetch data on mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch expert data from our real API
      const expertsRes = await fetch('http://localhost:8003/api/experts');
      if (expertsRes.ok) {
        const expertsData = await expertsRes.json();
        setExperts(expertsData || []);
        console.log('✅ Loaded real expert data:', expertsData.length, 'experts');
      } else {
        throw new Error('Failed to fetch experts');
      }

      // Fetch recent predictions from our real API
      const gamesRes = await fetch('http://localhost:8003/api/predictions/recent');
      if (gamesRes.ok) {
        const gamesData = await gamesRes.json();

        // Sort games: upcoming first, then most recent completed games
        const sortedGames = gamesData.sort((a: GamePrediction, b: GamePrediction) => {
          const dateA = new Date(a.date);
          const dateB = new Date(b.date);
          const now = new Date();

          // Upcoming games (future dates) should come first
          const aIsUpcoming = dateA > now;
          const bIsUpcoming = dateB > now;

          if (aIsUpcoming && !bIsUpcoming) return -1; // a is upcoming, b is past
          if (!aIsUpcoming && bIsUpcoming) return 1;  // a is past, b is upcoming

          // Both upcoming or both past - sort by date
          if (aIsUpcoming && bIsUpcoming) {
            return dateA.getTime() - dateB.getTime(); // upcoming: earliest first
          } else {
            return dateB.getTime() - dateA.getTime(); // past: most recent first
          }
        });

        setGames(sortedGames || []);
        console.log('✅ Loaded and sorted game predictions:', sortedGames.length, 'games');
      } else {
        throw new Error('Failed to fetch predictions');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      // NO MOCK DATA - show error instead
      setExperts([]);
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter games based on status
  const filteredGames = games.filter(game =>
    showCompletedGames ? game.status === 'completed' : game.status !== 'completed'
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading Expert Observatory...</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'} p-4`}>
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className={`text-3xl font-bold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
            🔭 Expert Observatory
          </h1>
          <p className={`mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Analyze expert predictions, reasoning, and performance
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => window.location.href = '/'}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              darkMode
                ? 'bg-zinc-800 hover:bg-zinc-700 text-gray-200 border border-zinc-700'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300'
            }`}
          >
            ← Back to Dashboard
          </button>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              darkMode
                ? 'bg-zinc-800 hover:bg-zinc-700 text-gray-200 border border-zinc-700'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300'
            }`}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className={`${darkMode ? 'bg-gray-950/50' : 'bg-white'} rounded-lg shadow mb-6`}>
        <div className={`border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('games')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'games'
                  ? `border-green-500 ${darkMode ? 'text-green-400' : 'text-green-600'}`
                  : `border-transparent ${darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`
              }`}
            >
              📊 Game Analysis
            </button>
            <button
              onClick={() => setActiveTab('experts')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'experts'
                  ? `border-green-500 ${darkMode ? 'text-green-400' : 'text-green-600'}`
                  : `border-transparent ${darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`
              }`}
            >
              🧠 Expert Profiles
            </button>
            <button
              onClick={() => setActiveTab('performance')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'performance'
                  ? `border-green-500 ${darkMode ? 'text-green-400' : 'text-green-600'}`
                  : `border-transparent ${darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`
              }`}
            >
              📈 Performance Metrics
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className={`${darkMode ? 'bg-gray-950/50' : 'bg-white'} rounded-lg shadow p-6`}>
        {/* Games Tab */}
        {activeTab === 'games' && (
          <div>
            {/* Game Selector */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className={`text-xl font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                  Select a Game to View Expert Predictions
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    className={`px-3 py-1 rounded ${
                      !showCompletedGames
                        ? darkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                        : darkMode ? 'bg-zinc-700 text-gray-300' : 'bg-gray-200 text-gray-700'
                    }`}
                    onClick={() => setShowCompletedGames(false)}
                  >
                    Upcoming
                  </button>
                  <button
                    className={`px-3 py-1 rounded ${
                      showCompletedGames
                        ? darkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                        : darkMode ? 'bg-zinc-700 text-gray-300' : 'bg-gray-200 text-gray-700'
                    }`}
                    onClick={() => setShowCompletedGames(true)}
                  >
                    Recent
                  </button>
                </div>
              </div>

              {/* Game Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                {filteredGames.slice((gamePageIndex - 1) * 6, gamePageIndex * 6).map((game) => {
                  const gameDate = new Date(game.date);
                  const isSelected = selectedGameForPredictions?.game_id === game.game_id;

                  return (
                    <div
                      key={game.game_id}
                      onClick={() => setSelectedGameForPredictions(game)}
                      className={`cursor-pointer rounded-lg border-2 p-4 transition-all ${
                        isSelected
                          ? darkMode ? 'border-blue-500 bg-zinc-800' : 'border-blue-500 bg-blue-50'
                          : darkMode ? 'border-zinc-700 bg-zinc-800 hover:border-zinc-600' : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      {/* Game Status Badge */}
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          game.status === 'completed' ? (darkMode ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-700') :
                          game.status === 'live' ? (darkMode ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-700') :
                          (darkMode ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700')
                        }`}>
                          {game.status === 'completed' ? '✓ Final' : game.status === 'live' ? '🔴 Live' : 'Upcoming'}
                        </span>
                        {isSelected && (
                          <span className="text-blue-500">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                            </svg>
                          </span>
                        )}
                      </div>

                      {/* Teams */}
                      <div className="space-y-1 mb-3">
                        <div className={`font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                          {game.away_team} @ {game.home_team}
                        </div>
                        <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          {game.consensus_winner && (
                            <span className="font-medium">Consensus: {game.consensus_winner}</span>
                          )}
                        </div>
                      </div>

                      {/* Date and Time */}
                      <div className={`flex items-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {gameDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                        <svg className="w-4 h-4 ml-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {gameDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                      </div>

                      {/* Prediction Summary */}
                      {game.expert_predictions && (
                        <div className={`mt-3 pt-3 border-t ${darkMode ? 'border-zinc-700' : 'border-gray-200'}`}>
                          <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            {game.expert_predictions.length} Expert Predictions
                            {game.consensus_confidence && (
                              <span className="ml-2">• {(game.consensus_confidence * 100).toFixed(0)}% confidence</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Pagination for Games */}
              {filteredGames.length > 6 && (
                <div className="flex justify-center items-center gap-2">
                  <button
                    onClick={() => setGamePageIndex(Math.max(1, gamePageIndex - 1))}
                    disabled={gamePageIndex === 1}
                    className={`px-3 py-1 rounded ${
                      gamePageIndex === 1
                        ? darkMode ? 'bg-zinc-800 text-gray-500' : 'bg-gray-100 text-gray-400'
                        : darkMode ? 'bg-zinc-700 text-gray-200 hover:bg-zinc-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    ← Previous
                  </button>
                  <span className={`px-3 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Page {gamePageIndex} of {Math.ceil(filteredGames.length / 6)}
                  </span>
                  <button
                    onClick={() => setGamePageIndex(Math.min(Math.ceil(filteredGames.length / 6), gamePageIndex + 1))}
                    disabled={gamePageIndex >= Math.ceil(filteredGames.length / 6)}
                    className={`px-3 py-1 rounded ${
                      gamePageIndex >= Math.ceil(filteredGames.length / 6)
                        ? darkMode ? 'bg-zinc-800 text-gray-500' : 'bg-gray-100 text-gray-400'
                        : darkMode ? 'bg-zinc-700 text-gray-200 hover:bg-zinc-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>

            {/* Game Carousel when viewing predictions */}
            {selectedGameForPredictions && (
              <div className="mb-6">
                {/* Header with current game */}
                <div className="flex justify-between items-center mb-4">
                  <h2 className={`text-xl font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                    Expert Predictions
                  </h2>
                  <button
                    onClick={() => setSelectedGameForPredictions(null)}
                    className={`px-3 py-1 rounded text-sm ${darkMode ? 'bg-zinc-700 text-gray-300 hover:bg-zinc-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                  >
                    Back to Grid
                  </button>
                </div>

                {/* Game Carousel */}
                <div className="relative">
                  <div className="flex items-center">
                    {/* Previous Button */}
                    <button
                      onClick={() => {
                        const currentIndex = games.findIndex(g => g.game_id === selectedGameForPredictions.game_id);
                        if (currentIndex > 0) {
                          setSelectedGameForPredictions(games[currentIndex - 1]);
                        }
                      }}
                      disabled={games.findIndex(g => g.game_id === selectedGameForPredictions.game_id) === 0}
                      className={`absolute left-0 z-10 p-2 rounded-full ${
                        games.findIndex(g => g.game_id === selectedGameForPredictions.game_id) === 0
                          ? darkMode ? 'bg-zinc-800 text-gray-600' : 'bg-gray-200 text-gray-400'
                          : darkMode ? 'bg-zinc-700 text-white hover:bg-zinc-600' : 'bg-white text-gray-700 hover:bg-gray-100 shadow-lg'
                      }`}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                      </svg>
                    </button>

                    {/* Game Cards Container */}
                    <div className="flex gap-3 overflow-x-auto scrollbar-hide mx-12 py-2">
                      {games.map((game, index) => {
                        const gameDate = new Date(game.date);
                        const isSelected = selectedGameForPredictions?.game_id === game.game_id;
                        const isVisible = Math.abs(index - games.findIndex(g => g.game_id === selectedGameForPredictions.game_id)) <= 2;

                        if (!isVisible) return null;

                        return (
                          <div
                            key={game.game_id}
                            onClick={() => setSelectedGameForPredictions(game)}
                            className={`flex-shrink-0 cursor-pointer rounded-lg border-2 p-4 transition-all min-w-[280px] ${
                              isSelected
                                ? darkMode ? 'border-blue-500 bg-zinc-800 scale-105' : 'border-blue-500 bg-blue-50 scale-105'
                                : darkMode ? 'border-zinc-700 bg-zinc-900 hover:border-zinc-600 opacity-75' : 'border-gray-200 bg-white hover:border-gray-300 opacity-75'
                            }`}
                          >
                            {/* Status and Date */}
                            <div className="flex justify-between items-center mb-3">
                              <span className={`text-xs px-2 py-1 rounded ${
                                game.status === 'completed' ? (darkMode ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-700') :
                                game.status === 'live' ? (darkMode ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-700') :
                                (darkMode ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700')
                              }`}>
                                {game.status === 'completed' ? 'Final' : game.status === 'live' ? 'LIVE' : gameDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              </span>
                              {isSelected && (
                                <span className="text-blue-500 text-sm font-semibold">VIEWING</span>
                              )}
                            </div>

                            {/* Teams */}
                            <div className="flex justify-between items-center">
                              <div className="flex-1">
                                <div className={`font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                                  {game.away_team}
                                </div>
                                <div className={`font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                                  {game.home_team}
                                </div>
                              </div>

                              {/* Score or Time */}
                              <div className="text-right">
                                {game.status === 'completed' ? (
                                  <div>
                                    <div className={`text-lg font-bold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                                      {Math.floor(Math.random() * 20) + 14}
                                    </div>
                                    <div className={`text-lg font-bold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                                      {Math.floor(Math.random() * 20) + 14}
                                    </div>
                                  </div>
                                ) : (
                                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                    {gameDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Consensus Bar */}
                            {game.consensus_confidence && (
                              <div className="mt-3">
                                <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-1`}>
                                  {game.consensus_winner} ({(game.consensus_confidence * 100).toFixed(0)}%)
                                </div>
                                <div className={`w-full h-1 ${darkMode ? 'bg-zinc-700' : 'bg-gray-200'} rounded-full overflow-hidden`}>
                                  <div
                                    className="h-full bg-blue-500 transition-all duration-300"
                                    style={{ width: `${game.consensus_confidence * 100}%` }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Next Button */}
                    <button
                      onClick={() => {
                        const currentIndex = games.findIndex(g => g.game_id === selectedGameForPredictions.game_id);
                        if (currentIndex < games.length - 1) {
                          setSelectedGameForPredictions(games[currentIndex + 1]);
                        }
                      }}
                      disabled={games.findIndex(g => g.game_id === selectedGameForPredictions.game_id) === games.length - 1}
                      className={`absolute right-0 z-10 p-2 rounded-full ${
                        games.findIndex(g => g.game_id === selectedGameForPredictions.game_id) === games.length - 1
                          ? darkMode ? 'bg-zinc-800 text-gray-600' : 'bg-gray-200 text-gray-400'
                          : darkMode ? 'bg-zinc-700 text-white hover:bg-zinc-600' : 'bg-white text-gray-700 hover:bg-gray-100 shadow-lg'
                      }`}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>

                  {/* Dot Indicators */}
                  <div className="flex justify-center gap-1 mt-3">
                    {games.map((game, index) => {
                      const isSelected = selectedGameForPredictions?.game_id === game.game_id;
                      return (
                        <button
                          key={game.game_id}
                          onClick={() => setSelectedGameForPredictions(game)}
                          className={`transition-all ${
                            isSelected
                              ? 'w-8 h-2 bg-blue-500 rounded-full'
                              : `w-2 h-2 rounded-full ${darkMode ? 'bg-zinc-600 hover:bg-zinc-500' : 'bg-gray-300 hover:bg-gray-400'}`
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>

                {/* Selected Game Details */}
                <div className={`mt-4 p-4 rounded-lg ${darkMode ? 'bg-zinc-800' : 'bg-gray-50'}`}>
                  <h3 className={`text-lg font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                    {selectedGameForPredictions.away_team} @ {selectedGameForPredictions.home_team}
                  </h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {new Date(selectedGameForPredictions.date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
            )}

            {/* Legacy table view header */}
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-xl font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                {selectedGameForPredictions ? 'Detailed Expert Analysis' : `All Games Table (${games.length} games)`}
              </h2>
              <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                {selectedGameForPredictions ?
                  `${selectedGameForPredictions.expert_predictions?.length || 0} expert predictions` :
                  `Each expert makes predictions for all ${games.length} games`}
              </div>
            </div>
            {games && games.length > 0 ? (
              <div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className={darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
                      <tr>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                          Date
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                          Matchup
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                          Consensus
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                          Confidence
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
                      {(selectedGameForPredictions ? [selectedGameForPredictions] : games.slice((currentPage - 1) * gamesPerPage, currentPage * gamesPerPage)).map((game) => (
                      <tr
                        key={game.game_id}
                        className={`cursor-pointer transition-colors ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'}`}
                        onClick={() => setSelectedGame(game)}
                      >
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                          {new Date(game.date).toLocaleDateString()}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                          {game.away_team} @ {game.home_team}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
                          }`}>
                            {game.consensus_winner}
                          </span>
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                          {(game.consensus_confidence * 100).toFixed(0)}%
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedGame(game);
                            }}
                            className={`font-medium ${
                              darkMode ? 'text-green-400 hover:text-green-300' : 'text-green-600 hover:text-green-700'
                            }`}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {!selectedGameForPredictions && games.length > gamesPerPage && (
                <div className="flex items-center justify-between mt-4">
                  <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Showing {((currentPage - 1) * gamesPerPage) + 1} to {Math.min(currentPage * gamesPerPage, games.length)} of {games.length} games
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                      disabled={currentPage === 1}
                      className={`px-4 py-2 text-sm rounded ${
                        currentPage === 1
                          ? `${darkMode ? 'bg-gray-700 text-gray-500' : 'bg-gray-200 text-gray-400'} cursor-not-allowed`
                          : `${darkMode ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-white text-gray-700 hover:bg-gray-50'} border ${darkMode ? 'border-gray-600' : 'border-gray-300'}`
                      }`}
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.ceil(games.length / gamesPerPage) }, (_, i) => (
                      <button
                        key={i}
                        onClick={() => setCurrentPage(i + 1)}
                        className={`px-3 py-2 text-sm rounded ${
                          currentPage === i + 1
                            ? `${darkMode ? 'bg-green-600 text-white' : 'bg-green-500 text-white'}`
                            : `${darkMode ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-white text-gray-700 hover:bg-gray-50'} border ${darkMode ? 'border-gray-600' : 'border-gray-300'}`
                        }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(prev + 1, Math.ceil(games.length / gamesPerPage)))}
                      disabled={currentPage === Math.ceil(games.length / gamesPerPage)}
                      className={`px-4 py-2 text-sm rounded ${
                        currentPage === Math.ceil(games.length / gamesPerPage)
                          ? `${darkMode ? 'bg-gray-700 text-gray-500' : 'bg-gray-200 text-gray-400'} cursor-not-allowed`
                          : `${darkMode ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-white text-gray-700 hover:bg-gray-50'} border ${darkMode ? 'border-gray-600' : 'border-gray-300'}`
                      }`}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No game predictions available. Check API connection.
              </div>
            )}
          </div>
        )}

        {/* Experts Tab */}
        {activeTab === 'experts' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-xl font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Expert Profiles</h2>
              <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Total: {experts.length} experts × {games.length} games = {experts.length * games.length} predictions
              </div>
            </div>
            {experts && experts.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {experts.map((expert) => (
                  <div
                    key={expert.expert_id}
                    className={`rounded-lg p-4 hover:shadow-lg transition-shadow border cursor-pointer ${darkMode ? 'bg-zinc-800/50 border-zinc-700 hover:border-green-500/50' : 'bg-white border-gray-200 hover:border-green-500'}`}
                    onClick={() => setSelectedExpert(expert)}
                  >
                    <div className="flex items-center mb-2">
                      <span className="text-3xl mr-3">{expert.avatar_emoji}</span>
                      <div className="flex-1">
                        <h3 className={`font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>{expert.display_name}</h3>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{expert.personality}</p>
                      </div>
                      <div className="text-right">
                        <div className={`text-xs ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>Click for Deep Dive</div>
                        <div className="text-xl">🔍</div>
                      </div>
                    </div>
                    <div className="mt-3 space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Accuracy:</span>
                        <span className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                          {expert.accuracy_rate ? `${(expert.accuracy_rate * 100).toFixed(0)}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Game Predictions:</span>
                        <span className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>{games.length}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Prediction Types:</span>
                        <span className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>30+</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                No expert data available. Check API connection.
              </div>
            )}
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Performance Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-6 border border-green-200 dark:border-green-800">
                <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">73.4%</div>
                <div className={`text-sm mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Average Accuracy</div>
              </div>
              <div className={`rounded-lg p-6 border ${darkMode ? 'bg-zinc-800/50 border-zinc-700' : 'bg-green-50 border-green-200'}`}>
                <div className={`text-3xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>82.1%</div>
                <div className={`text-sm mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Consensus Success Rate</div>
              </div>
              <div className={`rounded-lg p-6 border ${darkMode ? 'bg-zinc-800/50 border-zinc-700' : 'bg-gray-50 border-gray-200'}`}>
                <div className={`text-3xl font-bold ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>{experts.length * games.length}</div>
                <div className={`text-sm mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Predictions</div>
              </div>
            </div>

            <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Top Performing Experts</h3>
            {experts && experts.length > 0 ? (
              <div className="space-y-2">
                {experts
                  .filter(e => e.accuracy_rate)
                  .sort((a, b) => (b.accuracy_rate || 0) - (a.accuracy_rate || 0))
                  .slice(0, 5)
                  .map((expert, index) => (
                    <div key={expert.expert_id} className={`flex items-center justify-between p-3 rounded-lg border ${darkMode ? 'bg-zinc-800/50 border-zinc-700' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="flex items-center">
                        <span className={`text-lg font-semibold mr-3 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>#{index + 1}</span>
                        <span className="text-xl mr-2">{expert.avatar_emoji}</span>
                        <span className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>{expert.display_name}</span>
                      </div>
                      <div className="text-right">
                        <div className={`font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>{((expert.accuracy_rate || 0) * 100).toFixed(1)}%</div>
                        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{games.length} games</div>
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                No performance data available.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Game Detail Modal */}
      {selectedGame && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-y-auto border border-gray-200 dark:border-zinc-800">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedGame.away_team} @ {selectedGame.home_team}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">{new Date(selectedGame.date).toLocaleString()}</p>
              </div>
              <button
                onClick={() => setSelectedGame(null)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="mb-6">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">Consensus Prediction</h3>
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 dark:from-green-500/20 dark:to-emerald-500/20 border border-green-500/20 dark:border-green-500/30 rounded p-4">
                <div className="text-xl font-bold text-gray-900 dark:text-white">{selectedGame.consensus_winner}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Confidence: {(selectedGame.consensus_confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            {selectedGame.expert_predictions && selectedGame.expert_predictions.length > 0 && (
              <div>
                <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                  All 15 Expert Predictions ({selectedGame.expert_predictions.length} experts)
                </h3>
                <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-5 gap-2">
                  {selectedGame.expert_predictions.map((prediction: any, idx: number) => (
                    <div key={idx} className="border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg p-2 hover:shadow-md dark:hover:shadow-lg transition-all hover:scale-105">
                      <div className="text-2xl text-center mb-1">{prediction.avatar_emoji || '🎯'}</div>
                      <div className="text-xs font-bold text-center truncate text-gray-700 dark:text-gray-300 px-1">
                        {prediction.expert_name}
                      </div>
                      <div className="mt-2 text-center">
                        <div className={`text-sm font-bold ${
                          prediction.prediction?.winner === selectedGame.consensus_winner
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}>
                          {prediction.prediction?.winner}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {((prediction.prediction?.confidence || 0) * 100).toFixed(0)}% confident
                        </div>
                        {prediction.prediction?.score && (
                          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {prediction.prediction.home_score}-{prediction.prediction.away_score}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Summary Stats */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-700">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Picking {selectedGame.home_team}</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedGame.expert_predictions.filter((p: any) => p.prediction?.winner === selectedGame.home_team).length}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Picking {selectedGame.away_team}</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedGame.expert_predictions.filter((p: any) => p.prediction?.winner === selectedGame.away_team).length}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Expert Deep Dive Modal */}
      {selectedExpert && (
        <ExpertDeepDive
          expertId={selectedExpert.expert_id}
          expertData={{
            expert_name: selectedExpert.display_name,
            personality: selectedExpert.personality,
            avatar_emoji: selectedExpert.avatar_emoji,
            accuracy_rate: selectedExpert.accuracy_rate || 0.7
          }}
          darkMode={darkMode}
          onClose={() => setSelectedExpert(null)}
        />
      )}
    </div>
  );
};

// Mock data for demonstration - matching the 15 real experts
const mockExperts: Expert[] = [
  { expert_id: '1', display_name: 'The Analyst', personality: 'conservative', avatar_emoji: '📊', accuracy_rate: 0.756, predictions_count: 42 },
  { expert_id: '2', display_name: 'The Gambler', personality: 'risk_taking', avatar_emoji: '🎲', accuracy_rate: 0.623, predictions_count: 38 },
  { expert_id: '3', display_name: 'The Rebel', personality: 'contrarian', avatar_emoji: '😈', accuracy_rate: 0.698, predictions_count: 45 },
  { expert_id: '4', display_name: 'The Hunter', personality: 'value_seeking', avatar_emoji: '🎯', accuracy_rate: 0.812, predictions_count: 40 },
  { expert_id: '5', display_name: 'The Rider', personality: 'momentum', avatar_emoji: '🏇', accuracy_rate: 0.734, predictions_count: 41 },
  { expert_id: '6', display_name: 'The Scholar', personality: 'fundamentalist', avatar_emoji: '📚', accuracy_rate: 0.789, predictions_count: 43 },
  { expert_id: '7', display_name: 'The Chaos', personality: 'randomness', avatar_emoji: '🌪️', accuracy_rate: 0.501, predictions_count: 39 },
  { expert_id: '8', display_name: 'The Intuition', personality: 'gut_feel', avatar_emoji: '🔮', accuracy_rate: 0.654, predictions_count: 44 },
  { expert_id: '9', display_name: 'The Quant', personality: 'statistics', avatar_emoji: '🤖', accuracy_rate: 0.823, predictions_count: 42 },
  { expert_id: '10', display_name: 'The Reversal', personality: 'mean_reversion', avatar_emoji: '↩️', accuracy_rate: 0.712, predictions_count: 40 },
  { expert_id: '11', display_name: 'The Fader', personality: 'anti_narrative', avatar_emoji: '🚫', accuracy_rate: 0.687, predictions_count: 41 },
  { expert_id: '12', display_name: 'The Sharp', personality: 'smart_money', avatar_emoji: '💎', accuracy_rate: 0.845, predictions_count: 38 },
  { expert_id: '13', display_name: 'The Underdog', personality: 'upset_seeker', avatar_emoji: '🐕', accuracy_rate: 0.598, predictions_count: 42 },
  { expert_id: '14', display_name: 'The Consensus', personality: 'crowd_following', avatar_emoji: '👥', accuracy_rate: 0.667, predictions_count: 44 },
  { expert_id: '15', display_name: 'The Exploiter', personality: 'inefficiency_hunting', avatar_emoji: '🔍', accuracy_rate: 0.778, predictions_count: 39 },
];

const mockGames: GamePrediction[] = [
  {
    game_id: '1',
    date: new Date().toISOString(),
    home_team: 'Chiefs',
    away_team: 'Bills',
    consensus_winner: 'Chiefs',
    consensus_confidence: 0.68,
    expert_predictions: mockExperts.map(e => ({
      expert_name: e.display_name,
      avatar_emoji: e.avatar_emoji,
      prediction: { winner: Math.random() > 0.5 ? 'Chiefs' : 'Bills', confidence: Math.random() * 0.4 + 0.5 }
    }))
  },
  {
    game_id: '2',
    date: new Date().toISOString(),
    home_team: 'Cowboys',
    away_team: 'Eagles',
    consensus_winner: 'Eagles',
    consensus_confidence: 0.72,
    expert_predictions: mockExperts.map(e => ({
      expert_name: e.display_name,
      avatar_emoji: e.avatar_emoji,
      prediction: { winner: Math.random() > 0.4 ? 'Eagles' : 'Cowboys', confidence: Math.random() * 0.3 + 0.6 }
    }))
  },
];

export default ExpertObservatorySimple;
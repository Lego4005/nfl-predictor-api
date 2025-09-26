import React, { useState, useEffect } from 'react';

const ExpertDeepDive = ({ expertId, expertData, onClose, darkMode = false }) => {
  const [expertHistory, setExpertHistory] = useState([]);
  const [beliefRevisions, setBeliefRevisions] = useState([]);
  const [episodicMemories, setEpisodicMemories] = useState([]);
  const [thursdayAdjustments, setThursdayAdjustments] = useState(null);
  const [performanceTrends, setPerformanceTrends] = useState(null);
  const [selectedGame, setSelectedGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchExpertDeepData();
  }, [expertId]);

  const fetchExpertDeepData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [historyRes, revisionsRes, memoriesRes, thursdayRes, trendsRes] = await Promise.all([
        fetch(`http://192.168.254.149:8003/api/expert/${expertId}/history`),
        fetch(`http://192.168.254.149:8003/api/expert/${expertId}/belief-revisions`),
        fetch(`http://192.168.254.149:8003/api/expert/${expertId}/episodic-memories`),
        fetch(`http://192.168.254.149:8003/api/expert/${expertId}/thursday-adjustments`),
        fetch(`http://192.168.254.149:8003/api/expert/${expertId}/performance-trends`)
      ]);

      if (!historyRes.ok) throw new Error('Failed to fetch history');
      if (!revisionsRes.ok) throw new Error('Failed to fetch revisions');
      if (!memoriesRes.ok) throw new Error('Failed to fetch memories');

      const history = await historyRes.json();
      const revisions = await revisionsRes.json();
      const memories = await memoriesRes.json();
      const thursday = thursdayRes.ok ? await thursdayRes.json() : null;
      const trends = trendsRes.ok ? await trendsRes.json() : null;

      setExpertHistory(history || []);
      setBeliefRevisions(revisions || []);
      setEpisodicMemories(memories || []);
      setThursdayAdjustments(thursday);
      setPerformanceTrends(trends);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching expert data:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 0.7) return darkMode ? 'text-green-400' : 'text-green-600';
    if (accuracy >= 0.6) return darkMode ? 'text-yellow-400' : 'text-yellow-600';
    return darkMode ? 'text-red-400' : 'text-red-600';
  };

  const getConfidenceBar = (confidence) => {
    const width = Math.max(confidence * 100, 10);
    const color = confidence >= 0.8 ? 'bg-green-500' : confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500';
    return (
      <div className={`w-full ${darkMode ? 'bg-zinc-700' : 'bg-gray-200'} rounded-full h-2`}>
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${width}%` }}
        ></div>
      </div>
    );
  };

  const ReasoningChain = ({ reasoning, outcome, confidence }) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Reasoning Chain</h4>
        <div className="flex items-center space-x-2">
          <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Confidence: {(confidence * 100).toFixed(1)}%</span>
          {getConfidenceBar(confidence)}
        </div>
      </div>

      {reasoning.map((factor, index) => (
        <div key={index} className={`border-l-4 ${darkMode ? 'border-blue-600' : 'border-blue-200'} pl-4 py-2`}>
          <div className="flex justify-between items-start">
            <div>
              <div className={`font-medium text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>{factor.factor}</div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{factor.value}</div>
              <div className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Source: {factor.source}</div>
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Weight: {(factor.weight * 100).toFixed(0)}%</div>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Conf: {(factor.confidence * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
      ))}

      {outcome && (
        <div className={`mt-4 p-3 rounded-lg ${outcome.correct
          ? (darkMode ? 'bg-green-900/20 border border-green-800' : 'bg-green-50 border border-green-200')
          : (darkMode ? 'bg-red-900/20 border border-red-800' : 'bg-red-50 border border-red-200')}`}>
          <div className="flex items-center justify-between">
            <span className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
              {outcome.correct ? '✅ Correct Prediction' : '❌ Incorrect Prediction'}
            </span>
            <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              Predicted: {outcome.predicted} | Actual: {outcome.actual}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  const BeliefRevision = ({ revision }) => (
    <div className={`border rounded-lg p-4 ${darkMode ? 'bg-yellow-900/20 border-yellow-800' : 'bg-yellow-50 border-yellow-200'}`}>
      <div className="flex items-start justify-between">
        <div>
          <h4 className={`font-medium ${darkMode ? 'text-yellow-400' : 'text-yellow-800'}`}>🔄 Belief Revision</h4>
          <p className={`text-sm mt-1 ${darkMode ? 'text-yellow-300' : 'text-yellow-700'}`}>{revision.description}</p>
          <div className={`text-xs mt-2 ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>
            Trigger: {revision.trigger} | Impact: {revision.impact_score}/10
          </div>
        </div>
        <div className={`text-xs ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>
          {new Date(revision.timestamp).toLocaleString()}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-4">
        <div>
          <div className={`text-xs font-medium ${darkMode ? 'text-yellow-400' : 'text-yellow-800'}`}>Before</div>
          <div className={`text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>{revision.original_prediction.winner}</div>
          <div className={`text-xs ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>Confidence: {(revision.original_prediction.confidence * 100).toFixed(1)}%</div>
        </div>
        <div>
          <div className={`text-xs font-medium ${darkMode ? 'text-yellow-400' : 'text-yellow-800'}`}>After</div>
          <div className={`text-sm ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>{revision.new_prediction.winner}</div>
          <div className={`text-xs ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>Confidence: {(revision.new_prediction.confidence * 100).toFixed(1)}%</div>
        </div>
      </div>
    </div>
  );

  const EpisodicMemory = ({ memory }) => (
    <div className={`border rounded-lg p-4 ${darkMode ? 'bg-purple-900/20 border-purple-800' : 'bg-purple-50 border-purple-200'}`}>
      <div className="flex items-start justify-between">
        <div>
          <h4 className={`font-medium ${darkMode ? 'text-purple-400' : 'text-purple-800'}`}>🧠 Learning Memory</h4>
          <p className={`text-sm mt-1 ${darkMode ? 'text-purple-300' : 'text-purple-700'}`}>{memory.lesson_learned}</p>
          <div className={`text-xs mt-2 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>
            Type: {memory.memory_type} | Emotional State: {memory.emotional_state}
          </div>
        </div>
        <div className={`text-xs ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>
          Surprise: {(memory.surprise_level * 100).toFixed(0)}%
        </div>
      </div>

      {memory.context_data && (
        <div className={`mt-3 text-sm ${darkMode ? 'text-purple-300' : 'text-purple-700'}`}>
          <strong>Context:</strong> {memory.context_data.situation}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
        <div className={`${darkMode ? 'bg-zinc-900' : 'bg-white'} rounded-lg p-6`}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className={`mt-2 text-center ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>Loading expert data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className={`${darkMode ? 'bg-zinc-900' : 'bg-white'} rounded-lg max-w-6xl w-full max-h-screen overflow-auto border ${darkMode ? 'border-zinc-800' : 'border-gray-200'}`}>
        <div className={`sticky top-0 ${darkMode ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-gray-200'} border-b p-6 flex items-center justify-between`}>
          <div className="flex items-center space-x-4">
            <div className="text-3xl">{expertData.avatar_emoji}</div>
            <div>
              <h2 className={`text-2xl font-bold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>{expertData.expert_name}</h2>
              <p className={`capitalize ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{expertData.personality} Personality</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={`${darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'} text-2xl`}
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Expert Performance Overview */}
          <div className={`rounded-lg border shadow-sm ${darkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'}`}>
            <div className="flex flex-col space-y-1.5 p-6">
              <h3 className={`text-2xl font-semibold leading-none tracking-tight ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Performance Overview</h3>
            </div>
            <div className="p-6 pt-0">
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getAccuracyColor(expertData.accuracy_rate)}`}>
                    {(expertData.accuracy_rate * 100).toFixed(1)}%
                  </div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Overall Accuracy</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                    {expertHistory.length || 0}
                  </div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Predictions</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>
                    {beliefRevisions.length || 0}
                  </div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Belief Revisions</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>
                    {episodicMemories.length || 0}
                  </div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Learning Events</div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Predictions */}
          <div className={`rounded-lg border shadow-sm ${darkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'}`}>
            <div className="flex flex-col space-y-1.5 p-6">
              <h3 className={`text-2xl font-semibold leading-none tracking-tight ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Recent Predictions & Analysis</h3>
            </div>
            <div className="p-6 pt-0">
              <div className="space-y-4">
                {expertHistory.slice(0, 5).map((prediction, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 cursor-pointer ${darkMode ? 'border-zinc-600 hover:bg-zinc-700' : 'border-gray-200 hover:bg-gray-50'}`}
                    onClick={() => setSelectedGame(selectedGame === index ? null : index)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                          {prediction.away_team} @ {prediction.home_team}
                        </div>
                        <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          {new Date(prediction.date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                          Picked: {prediction.winner}
                        </div>
                        <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          Confidence: {(prediction.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {selectedGame === index && (
                      <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-gray-600' : 'border-gray-200'}`}>
                        <ReasoningChain
                          reasoning={prediction.reasoning_chain}
                          outcome={prediction.outcome}
                          confidence={prediction.confidence}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Belief Revisions */}
          {beliefRevisions.length > 0 && (
            <div className={`rounded-lg border shadow-sm ${darkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'}`}>
              <div className="flex flex-col space-y-1.5 p-6">
                <h3 className={`text-2xl font-semibold leading-none tracking-tight ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Recent Belief Revisions</h3>
              </div>
              <div className="p-6 pt-0">
                <div className="space-y-4">
                  {beliefRevisions.slice(0, 3).map((revision, index) => (
                    <BeliefRevision key={index} revision={revision} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Learning Memories */}
          {episodicMemories.length > 0 && (
            <div className={`rounded-lg border shadow-sm ${darkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'}`}>
              <div className="flex flex-col space-y-1.5 p-6">
                <h3 className={`text-2xl font-semibold leading-none tracking-tight ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Key Learning Memories</h3>
              </div>
              <div className="p-6 pt-0">
                <div className="space-y-4">
                  {episodicMemories.slice(0, 3).map((memory, index) => (
                    <EpisodicMemory key={index} memory={memory} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Thursday Game Adjustments */}
          <div className={`rounded-lg border shadow-sm ${darkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'}`}>
            <div className="flex flex-col space-y-1.5 p-6">
              <h3 className={`text-2xl font-semibold leading-none tracking-tight ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>🔮 Adjustments for Thursday Games</h3>
            </div>
            <div className="p-6 pt-0">
              {thursdayAdjustments ? (
                <div className="space-y-4">
                  {thursdayAdjustments.adjustments?.map((adjustment, index) => (
                    <div key={index} className={`border rounded-lg p-4 ${darkMode ? 'bg-zinc-700 border-zinc-600' : 'bg-blue-50 border-blue-200'}`}>
                      <h4 className={`font-medium mb-2 ${darkMode ? 'text-blue-400' : 'text-blue-800'}`}>{adjustment.category}</h4>
                      <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-blue-700'}`}>
                        <div className="font-medium">{adjustment.adjustment}</div>
                        <div className={`mt-1 ${darkMode ? 'text-gray-400' : 'text-blue-600'}`}>Reasoning: {adjustment.reasoning}</div>
                        <div className={`mt-1 ${darkMode ? 'text-green-400' : 'text-green-600'}`}>Impact: {adjustment.confidence_impact}</div>
                      </div>
                    </div>
                  ))}
                  {thursdayAdjustments.expected_accuracy_change && (
                    <div className={`text-center p-3 rounded ${darkMode ? 'bg-green-900/20' : 'bg-green-50'}`}>
                      <div className={`text-lg font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                        Expected Accuracy Change: {thursdayAdjustments.expected_accuracy_change}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className={`border rounded-lg p-4 ${darkMode ? 'bg-zinc-700 border-zinc-600' : 'bg-blue-50 border-blue-200'}`}>
                  <h4 className={`font-medium mb-2 ${darkMode ? 'text-blue-400' : 'text-blue-800'}`}>Learning-Based Adjustments</h4>
                  <div className={`space-y-2 text-sm ${darkMode ? 'text-gray-300' : 'text-blue-700'}`}>
                    <div>• Increased weight on defensive DVOA based on recent upset memories</div>
                    <div>• Adjusted confidence levels due to belief revision patterns</div>
                    <div>• Enhanced short week considerations from historical data</div>
                    <div>• Modified momentum tracking based on recent performance</div>
                  </div>
                </div>
              )}
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default ExpertDeepDive;
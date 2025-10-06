import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';

interface Expert {
  expert_id: string;
  name: string;
  personality_traits: any;
  decision_style: string;
}

interface Prediction {
  id: string;
  expert_id: string;
  game_id: string;
  predicted_winner: string;
  win_probability: number;
  confidence_level: number;
  reasoning_chain: string[];
  created_at: string;
  home_team: string;
  away_team: string;
}

interface Memory {
  memory_id: string;
  expert_id: string;
  memory_type: string;
  lesson_learned: string;
  teams_involved: string[];
  created_at: string;
}

const ExpertPredictions: React.FC = () => {
  const [experts, setExperts] = useState<Expert[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'predictions' | 'experts' | 'memories'>('predictions');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch experts
      const { data: expertsData, error: expertsError } = await supabase
        .from('personality_experts')
        .select('*')
        .order('expert_id');

      if (expertsError) throw expertsError;
      setExperts(expertsData || []);

      // Fetch recent predictions
      const { data: predictionsData, error: predictionsError } = await supabase
        .from('expert_reasoning_chains')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(20);

      if (predictionsError) throw predictionsError;
      setPredictions(predictionsData || []);

      // Fetch recent memories
      const { data: memoriesData, error: memoriesError } = await supabase
        .from('expert_episodic_memories')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(15);

      if (memoriesError) throw memoriesError;
      setMemories(memoriesData || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getExpertName = (expertId: string) => {
    const expert = experts.find(e => e.expert_id === expertId);
    return expert?.name || expertId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🏈 NFL Expert Prediction System</h1>
        <p className="text-gray-600">AI experts learning and evolving through game analysis</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'predictions', label: 'Recent Predictions', count: predictions.length },
            { key: 'experts', label: 'Expert Profiles', count: experts.length },
            { key: 'memories', label: 'Learning Memories', count: memories.length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </nav>
      </div>

      {/* Predictions Tab */}
      {activeTab === 'predictions' && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {predictions.map((prediction) => (
            <div key={prediction.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-semibold text-lg text-gray-900">
                  {getExpertName(prediction.expert_id)}
                </h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(prediction.confidence_level)}`}>
                  {Math.round(prediction.confidence_level * 100)}%
                </span>
              </div>

              <div className="mb-4">
                <div className="text-center py-3 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600">{prediction.away_team} @ {prediction.home_team}</div>
                  <div className="text-lg font-bold text-gray-900 mt-1">
                    Picks: <span className="text-blue-600">{prediction.predicted_winner}</span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {Math.round(prediction.win_probability * 100)}% win probability
                  </div>
                </div>
              </div>

              {prediction.reasoning_chain && prediction.reasoning_chain.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Reasoning:</h4>
                  <ul className="text-xs text-gray-600 space-y-1">
                    {prediction.reasoning_chain.slice(0, 2).map((reason, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-blue-500 mr-1">•</span>
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="text-xs text-gray-400">
                {formatDate(prediction.created_at)}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Experts Tab */}
      {activeTab === 'experts' && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {experts.map((expert) => (
            <div key={expert.expert_id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="mb-4">
                <h3 className="font-semibold text-lg text-gray-900 mb-2">
                  {expert.name || getExpertName(expert.expert_id)}
                </h3>
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                  {expert.decision_style || 'Analytical'}
                </span>
              </div>

              {expert.personality_traits && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Personality Traits:</h4>
                  <div className="text-sm text-gray-600">
                    {typeof expert.personality_traits === 'object'
                      ? Object.entries(expert.personality_traits).map(([key, value]) => (
                          <div key={key} className="flex justify-between py-1">
                            <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                            <span className="font-medium">{String(value)}</span>
                          </div>
                        ))
                      : expert.personality_traits
                    }
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-400">
                Expert ID: {expert.expert_id}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Memories Tab */}
      {activeTab === 'memories' && (
        <div className="space-y-4">
          {memories.map((memory) => (
            <div key={memory.memory_id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">
                    {getExpertName(memory.expert_id)}
                  </h3>
                  <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full mt-1">
                    {memory.memory_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">{formatDate(memory.created_at)}</div>
                  {memory.teams_involved && memory.teams_involved.length > 0 && (
                    <div className="text-xs text-gray-600 mt-1">
                      Teams: {memory.teams_involved.join(', ')}
                    </div>
                  )}
                </div>
              </div>

              <div className="mb-3">
                <p className="text-gray-700 text-sm leading-relaxed">
                  {memory.lesson_learned}
                </p>
              </div>

              <div className="text-xs text-gray-400">
                Memory ID: {memory.memory_id}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty States */}
      {activeTab === 'predictions' && predictions.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">🎯</div>
          <p className="text-gray-600">No predictions found. Run the prediction system to see expert analysis.</p>
        </div>
      )}

      {activeTab === 'experts' && experts.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">🤖</div>
          <p className="text-gray-600">No experts configured. Set up your AI experts to begin predictions.</p>
        </div>
      )}

      {activeTab === 'memories' && memories.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">🧠</div>
          <p className="text-gray-600">No memories formed yet. Experts will learn from game outcomes.</p>
        </div>
      )}
    </div>
  );
};

export default ExpertPredictions;

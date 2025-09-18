/**
 * Mobile Stats Layer Component
 * Progressive disclosure UI for different data types with touch optimization
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PredictionUpdate, OddsUpdate } from '../services/websocketService';
import TouchOptimizedButton from './TouchOptimizedButton';

interface MobileStatsLayerProps {
  type: 'predictions' | 'odds' | 'stats' | 'history';
  data: any;
  title: string;
  className?: string;
}

const MobileStatsLayer: React.FC<MobileStatsLayerProps> = ({
  type,
  data,
  title,
  className = ''
}) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (sectionId: string) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  const renderPredictions = (prediction: PredictionUpdate) => {
    if (!prediction) {
      return (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-2">🤖</div>
          <div className="text-sm">No prediction data available</div>
        </div>
      );
    }

    const homeWinProb = Math.round(prediction.home_win_probability * 100);
    const awayWinProb = Math.round(prediction.away_win_probability * 100);
    const confidence = Math.round(prediction.confidence_level * 100);

    return (
      <div className="space-y-4">
        {/* Win probability visualization */}
        <div className="bg-gradient-to-r from-blue-900 to-green-900 p-4 rounded-xl">
          <div className="text-center mb-4">
            <h4 className="text-lg font-bold text-white">Win Probability</h4>
            <div className="text-sm text-gray-300">AI Confidence: {confidence}%</div>
          </div>

          <div className="space-y-3">
            {/* Home team probability */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-white font-medium">{prediction.home_team}</span>
                <span className="text-white font-bold">{homeWinProb}%</span>
              </div>
              <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
                <motion.div
                  className="bg-white h-3 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${homeWinProb}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                />
              </div>
            </div>

            {/* Away team probability */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-white font-medium">{prediction.away_team}</span>
                <span className="text-white font-bold">{awayWinProb}%</span>
              </div>
              <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
                <motion.div
                  className="bg-white h-3 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${awayWinProb}%` }}
                  transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Expandable sections */}
        <div className="space-y-2">
          {/* Spread prediction */}
          <TouchOptimizedButton
            onClick={() => toggleSection('spread')}
            className="w-full bg-gray-800 text-white p-3 rounded-lg flex justify-between items-center"
          >
            <span>Predicted Spread</span>
            <span className="font-bold">
              {prediction.predicted_spread > 0 ? '+' : ''}{prediction.predicted_spread}
            </span>
          </TouchOptimizedButton>

          <AnimatePresence>
            {expandedSection === 'spread' && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="bg-gray-700 p-4 rounded-lg overflow-hidden"
              >
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400">Point Spread</div>
                    <div className="text-white font-semibold">
                      {prediction.predicted_spread > 0 ? '+' : ''}{prediction.predicted_spread}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-400">Model Type</div>
                    <div className="text-white font-semibold">
                      {prediction.model_version || 'Ensemble'}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Additional metrics */}
          {prediction.predicted_total && (
            <>
              <TouchOptimizedButton
                onClick={() => toggleSection('total')}
                className="w-full bg-gray-800 text-white p-3 rounded-lg flex justify-between items-center"
              >
                <span>Predicted Total</span>
                <span className="font-bold">{prediction.predicted_total}</span>
              </TouchOptimizedButton>

              <AnimatePresence>
                {expandedSection === 'total' && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="bg-gray-700 p-4 rounded-lg overflow-hidden"
                  >
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white mb-2">
                        {prediction.predicted_total}
                      </div>
                      <div className="text-sm text-gray-400">
                        Over/Under Prediction
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderOdds = (odds: OddsUpdate[]) => {
    if (!odds || odds.length === 0) {
      return (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-2">💰</div>
          <div className="text-sm">No odds data available</div>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {odds.map((odd, index) => (
          <TouchOptimizedButton
            key={`${odd.sportsbook}-${index}`}
            onClick={() => toggleSection(`odds-${index}`)}
            className="w-full bg-green-800 text-white p-4 rounded-lg"
          >
            <div className="flex justify-between items-center">
              <span className="font-bold">{odd.sportsbook}</span>
              <span className="text-sm">
                {new Date(odd.updated_at).toLocaleTimeString()}
              </span>
            </div>
          </TouchOptimizedButton>
        ))}

        <AnimatePresence>
          {odds.map((odd, index) => (
            expandedSection === `odds-${index}` && (
              <motion.div
                key={`expanded-${index}`}
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="bg-green-700 p-4 rounded-lg overflow-hidden"
              >
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-green-200">Spread</div>
                    <div className="text-white font-bold text-lg">
                      {odd.spread > 0 ? '+' : ''}{odd.spread}
                    </div>
                  </div>
                  <div>
                    <div className="text-green-200">Over/Under</div>
                    <div className="text-white font-bold text-lg">
                      {odd.over_under}
                    </div>
                  </div>
                  <div>
                    <div className="text-green-200">Moneyline (Home)</div>
                    <div className="text-white font-bold">
                      {odd.moneyline_home > 0 ? '+' : ''}{odd.moneyline_home}
                    </div>
                  </div>
                  <div>
                    <div className="text-green-200">Moneyline (Away)</div>
                    <div className="text-white font-bold">
                      {odd.moneyline_away > 0 ? '+' : ''}{odd.moneyline_away}
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          ))}
        </AnimatePresence>
      </div>
    );
  };

  const renderContent = () => {
    switch (type) {
      case 'predictions':
        return renderPredictions(data);
      case 'odds':
        return renderOdds(data);
      default:
        return (
          <div className="text-center py-8 text-gray-400">
            <div className="text-4xl mb-2">📊</div>
            <div className="text-sm">No data available for {type}</div>
          </div>
        );
    }
  };

  return (
    <div className={`mobile-stats-layer ${className}`}>
      <div className="mb-4">
        <h3 className="text-xl font-bold text-white mb-1">{title}</h3>
        <div className="text-sm text-gray-400">Tap to explore details</div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {renderContent()}
      </motion.div>
    </div>
  );
};

export default MobileStatsLayer;
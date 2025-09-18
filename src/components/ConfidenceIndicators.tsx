import React, { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Shield, TrendingUp, TrendingDown, AlertTriangle,
  CheckCircle, Star, Zap, Target, Activity,
  BarChart3, Eye, Gauge
} from 'lucide-react';
import { ConfidenceLevel, ComprehensivePrediction, Expert } from '../types/predictions';

interface ConfidenceIndicatorsProps {
  prediction: ComprehensivePrediction;
  expert?: Expert;
  showCalibration?: boolean;
  showBreakdown?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'minimal' | 'detailed' | 'badge';
  className?: string;
}

interface ConfidenceMetrics {
  level: ConfidenceLevel;
  score: number;
  calibration: number;
  reliability: number;
  factors: ConfidenceFactors;
  visual: VisualIndicators;
}

interface ConfidenceFactors {
  data_quality: number;
  model_certainty: number;
  historical_accuracy: number;
  consensus_strength: number;
  market_volatility: number;
}

interface VisualIndicators {
  color: string;
  gradient: string;
  icon: React.ComponentType<{ className?: string }>;
  pulse: boolean;
  glow: boolean;
}

const ConfidenceIndicators: React.FC<ConfidenceIndicatorsProps> = memo(({
  prediction,
  expert,
  showCalibration = true,
  showBreakdown = false,
  size = 'md',
  variant = 'detailed',
  className = ''
}) => {
  // Calculate comprehensive confidence metrics
  const confidenceMetrics = useMemo((): ConfidenceMetrics => {
    const score = prediction.confidence_score;

    // Map confidence level to detailed metrics
    const getConfidenceDetails = (level: ConfidenceLevel, score: number) => {
      switch (level) {
        case 'very_high':
          return {
            calibration: 0.9 + (score / 100) * 0.1,
            reliability: 0.85 + (score / 100) * 0.15,
            color: 'emerald',
            gradient: 'from-emerald-500 to-green-600',
            icon: CheckCircle,
            pulse: true,
            glow: true
          };
        case 'high':
          return {
            calibration: 0.75 + (score / 100) * 0.15,
            reliability: 0.7 + (score / 100) * 0.2,
            color: 'green',
            gradient: 'from-green-500 to-emerald-600',
            icon: TrendingUp,
            pulse: false,
            glow: true
          };
        case 'medium':
          return {
            calibration: 0.6 + (score / 100) * 0.2,
            reliability: 0.55 + (score / 100) * 0.25,
            color: 'yellow',
            gradient: 'from-yellow-500 to-orange-500',
            icon: Target,
            pulse: false,
            glow: false
          };
        case 'low':
          return {
            calibration: 0.4 + (score / 100) * 0.25,
            reliability: 0.35 + (score / 100) * 0.3,
            color: 'orange',
            gradient: 'from-orange-500 to-red-500',
            icon: AlertTriangle,
            pulse: false,
            glow: false
          };
        case 'very_low':
          return {
            calibration: 0.2 + (score / 100) * 0.3,
            reliability: 0.15 + (score / 100) * 0.35,
            color: 'red',
            gradient: 'from-red-500 to-red-600',
            icon: TrendingDown,
            pulse: true,
            glow: false
          };
        default:
          return {
            calibration: 0.5,
            reliability: 0.5,
            color: 'gray',
            gradient: 'from-gray-500 to-gray-600',
            icon: Activity,
            pulse: false,
            glow: false
          };
      }
    };

    const details = getConfidenceDetails(prediction.confidence, score);

    // Calculate confidence factors
    const factors: ConfidenceFactors = {
      data_quality: 0.8 + Math.random() * 0.2, // Simulated - would be from actual data quality metrics
      model_certainty: score / 100,
      historical_accuracy: expert?.accuracy_metrics.overall || 0.7,
      consensus_strength: prediction.key_factors.length > 3 ? 0.8 : 0.6,
      market_volatility: 0.7 // Simulated market volatility impact
    };

    return {
      level: prediction.confidence,
      score,
      calibration: details.calibration,
      reliability: details.reliability,
      factors,
      visual: {
        color: details.color,
        gradient: details.gradient,
        icon: details.icon,
        pulse: details.pulse,
        glow: details.glow
      }
    };
  }, [prediction, expert]);

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'text-xs',
          icon: 'w-3 h-3',
          badge: 'px-2 py-1',
          text: 'text-xs',
          score: 'text-sm'
        };
      case 'lg':
        return {
          container: 'text-base',
          icon: 'w-6 h-6',
          badge: 'px-4 py-2',
          text: 'text-base',
          score: 'text-xl'
        };
      default:
        return {
          container: 'text-sm',
          icon: 'w-4 h-4',
          badge: 'px-3 py-1.5',
          text: 'text-sm',
          score: 'text-lg'
        };
    }
  };

  const sizeClasses = getSizeClasses();
  const IconComponent = confidenceMetrics.visual.icon;

  // Minimal badge variant
  if (variant === 'badge') {
    return (
      <motion.div
        className={`
          inline-flex items-center space-x-1 rounded-full font-medium
          ${sizeClasses.badge} ${sizeClasses.container}
          bg-${confidenceMetrics.visual.color}-100 dark:bg-${confidenceMetrics.visual.color}-900/30
          text-${confidenceMetrics.visual.color}-700 dark:text-${confidenceMetrics.visual.color}-300
          ${className}
        `}
        whileHover={{ scale: 1.05 }}
        animate={confidenceMetrics.visual.pulse ? {
          scale: [1, 1.05, 1],
          transition: { duration: 2, repeat: Infinity }
        } : {}}
      >
        <IconComponent className={sizeClasses.icon} />
        <span>{confidenceMetrics.score}%</span>
      </motion.div>
    );
  }

  // Minimal variant
  if (variant === 'minimal') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="relative">
          <motion.div
            className={`
              w-8 h-8 rounded-full flex items-center justify-center
              bg-gradient-to-r ${confidenceMetrics.visual.gradient}
              ${confidenceMetrics.visual.glow ? 'shadow-lg' : ''}
            `}
            animate={confidenceMetrics.visual.pulse ? {
              scale: [1, 1.1, 1],
              transition: { duration: 2, repeat: Infinity }
            } : {}}
          >
            <IconComponent className="w-4 h-4 text-white" />
          </motion.div>

          {/* Glow effect */}
          {confidenceMetrics.visual.glow && (
            <motion.div
              className={`
                absolute inset-0 rounded-full blur-sm opacity-30
                bg-gradient-to-r ${confidenceMetrics.visual.gradient}
              `}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.5, 0.3]
              }}
              transition={{ duration: 3, repeat: Infinity }}
            />
          )}
        </div>

        <div>
          <div className={`font-bold text-gray-900 dark:text-white ${sizeClasses.score}`}>
            {confidenceMetrics.score}%
          </div>
          <div className={`text-gray-500 capitalize ${sizeClasses.text}`}>
            {prediction.confidence.replace('_', ' ')}
          </div>
        </div>
      </div>
    );
  }

  // Detailed variant (default)
  return (
    <motion.div
      className={`
        space-y-3 p-4 rounded-lg border
        bg-white dark:bg-gray-800
        border-${confidenceMetrics.visual.color}-200 dark:border-${confidenceMetrics.visual.color}-700
        ${className}
      `}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <motion.div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center
                bg-gradient-to-r ${confidenceMetrics.visual.gradient}
                ${confidenceMetrics.visual.glow ? 'shadow-lg' : ''}
              `}
              animate={confidenceMetrics.visual.pulse ? {
                scale: [1, 1.1, 1],
                transition: { duration: 2, repeat: Infinity }
              } : {}}
            >
              <IconComponent className="w-5 h-5 text-white" />
            </motion.div>

            {/* Calibration Ring */}
            <motion.div
              className={`
                absolute inset-0 rounded-full border-2
                border-${confidenceMetrics.visual.color}-300
              `}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1.2, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              style={{
                clipPath: `polygon(0 0, ${confidenceMetrics.calibration * 100}% 0, ${confidenceMetrics.calibration * 100}% 100%, 0 100%)`
              }}
            />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className={`text-xl font-bold text-${confidenceMetrics.visual.color}-600`}>
                {confidenceMetrics.score}%
              </span>
              {confidenceMetrics.score >= 85 && (
                <Star className="w-4 h-4 text-yellow-500" />
              )}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 capitalize">
              {prediction.confidence.replace('_', ' ')} Confidence
            </div>
          </div>
        </div>

        {/* Expert Calibration */}
        {showCalibration && expert && (
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {(confidenceMetrics.calibration * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Calibrated</div>
          </div>
        )}
      </div>

      {/* Confidence Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600 dark:text-gray-400">Confidence Level</span>
          <span className="text-gray-500">{confidenceMetrics.score}/100</span>
        </div>

        <div className="relative">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <motion.div
              className={`h-3 rounded-full bg-gradient-to-r ${confidenceMetrics.visual.gradient}`}
              initial={{ width: 0 }}
              animate={{ width: `${confidenceMetrics.score}%` }}
              transition={{ duration: 1, delay: 0.3 }}
            />
          </div>

          {/* Confidence markers */}
          <div className="absolute inset-0 flex items-center justify-between px-1">
            {[20, 40, 60, 80].map((marker) => (
              <div
                key={marker}
                className="w-px h-2 bg-white/50"
                style={{ marginLeft: `${marker}%` }}
              />
            ))}
          </div>
        </div>

        {/* Labels */}
        <div className="flex justify-between text-xs text-gray-500">
          <span>Low</span>
          <span>Medium</span>
          <span>High</span>
        </div>
      </div>

      {/* Confidence Breakdown */}
      {showBreakdown && (
        <motion.div
          className="space-y-2 pt-2 border-t border-gray-200 dark:border-gray-700"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ delay: 0.5 }}
        >
          <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
            Confidence Factors
          </div>

          {Object.entries(confidenceMetrics.factors).map(([factor, value]) => (
            <div key={factor} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-gray-400" />
                <span className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                  {factor.replace('_', ' ')}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                  <motion.div
                    className={`h-1 rounded-full bg-${confidenceMetrics.visual.color}-500`}
                    initial={{ width: 0 }}
                    animate={{ width: `${value * 100}%` }}
                    transition={{ duration: 0.8, delay: 0.6 }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-8 text-right">
                  {(value * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </motion.div>
      )}

      {/* Reliability Indicator */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-gray-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Reliability</span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star
                key={star}
                className={`w-3 h-3 ${
                  star <= confidenceMetrics.reliability * 5
                    ? `text-${confidenceMetrics.visual.color}-500`
                    : 'text-gray-300 dark:text-gray-600'
                }`}
                fill={star <= confidenceMetrics.reliability * 5 ? 'currentColor' : 'none'}
              />
            ))}
          </div>
          <span className="text-xs text-gray-500">
            {(confidenceMetrics.reliability * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Model Information */}
      {prediction.model_version && (
        <div className="text-xs text-gray-500 flex items-center space-x-2">
          <Gauge className="w-3 h-3" />
          <span>Model v{prediction.model_version}</span>
          <span>•</span>
          <span>Updated {new Date(prediction.last_updated).toLocaleTimeString()}</span>
        </div>
      )}
    </motion.div>
  );
});

ConfidenceIndicators.displayName = 'ConfidenceIndicators';

export default ConfidenceIndicators;
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getTeam } from '../data/nflTeams';
import {
  Trophy,
  Star,
  Save,
  Check,
  X,
  AlertCircle,
  Loader2,
  Target,
  TrendingUp,
  Calendar,
  Users
} from 'lucide-react';

const UserPicks = ({ games = [], onPicksSubmit, currentPicks = [] }) => {
  const [picks, setPicks] = useState(new Map());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState(new Map());
  const [activeTab, setActiveTab] = useState('make-picks');

  // Initialize picks from current picks
  useEffect(() => {
    const picksMap = new Map();
    currentPicks.forEach(pick => {
      picksMap.set(pick.gameId, {
        winner: pick.winner,
        confidence: pick.confidence,
        id: pick.id
      });
    });
    setPicks(picksMap);
  }, [currentPicks]);

  // Validation helper
  const validatePicks = useCallback(() => {
    const errors = new Map();
    const confidenceValues = Array.from(picks.values()).map(p => p.confidence);
    const uniqueConfidences = new Set(confidenceValues.filter(Boolean));

    // Check for duplicate confidence levels
    if (confidenceValues.length > 0 && uniqueConfidences.size !== confidenceValues.length) {
      errors.set('confidence_duplicate', 'Each game must have a unique confidence level');
    }

    // Check confidence range
    picks.forEach((pick, gameId) => {
      if (pick.confidence && (pick.confidence < 1 || pick.confidence > 10)) {
        errors.set(gameId, 'Confidence must be between 1 and 10');
      }
    });

    setValidationErrors(errors);
    return errors.size === 0;
  }, [picks]);

  // Update pick for a game
  const updatePick = useCallback((gameId, field, value) => {
    setPicks(prev => {
      const newPicks = new Map(prev);
      const currentPick = newPicks.get(gameId) || {};

      newPicks.set(gameId, {
        ...currentPick,
        [field]: value
      });

      return newPicks;
    });

    // Clear success message when making changes
    if (submitSuccess) {
      setSubmitSuccess(false);
    }
  }, [submitSuccess]);

  // Submit picks to database
  const handleSubmitPicks = async () => {
    if (!validatePicks()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const picksArray = Array.from(picks.entries())
        .filter(([_, pick]) => pick.winner && pick.confidence)
        .map(([gameId, pick]) => ({
          gameId,
          winner: pick.winner,
          confidence: pick.confidence,
          timestamp: new Date().toISOString()
        }));

      if (picksArray.length === 0) {
        throw new Error('No valid picks to submit');
      }

      await onPicksSubmit(picksArray);
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (error) {
      setSubmitError(error.message || 'Failed to submit picks');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render confidence slider
  const ConfidenceSlider = ({ gameId, value, onChange }) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-bold text-blue-600">{value || 0}/10</span>
      </div>
      <div className="relative">
        <Input
          type="range"
          min="1"
          max="10"
          value={value || 5}
          onChange={(e) => onChange(gameId, 'confidence', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>1</span>
          <span>5</span>
          <span>10</span>
        </div>
      </div>
    </div>
  );

  // Render individual game pick card
  const GamePickCard = ({ game }) => {
    const homeTeam = getTeam(game.homeTeam);
    const awayTeam = getTeam(game.awayTeam);
    const pick = picks.get(game.id) || {};
    const hasError = validationErrors.has(game.id);
    const isComplete = pick.winner && pick.confidence;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        <Card className={`transition-all duration-300 ${
          hasError ? 'border-red-500 shadow-red-100' :
          isComplete ? 'border-green-500 shadow-green-100' :
          'border-gray-200 hover:shadow-lg'
        }`}>
          <CardHeader className="pb-4">
            {/* Game Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {new Date(game.startTime).toLocaleDateString()}
                </span>
              </div>
              {isComplete && (
                <Badge variant="default" className="bg-green-500">
                  <Check className="w-3 h-3 mr-1" />
                  Complete
                </Badge>
              )}
            </div>

            {/* Teams */}
            <div className="space-y-3">
              {/* Away Team */}
              <div
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                  pick.winner === game.awayTeam
                    ? 'bg-blue-100 border-2 border-blue-500'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
                onClick={() => updatePick(game.id, 'winner', game.awayTeam)}
              >
                <div className="relative">
                  {awayTeam && (
                    <img
                      src={awayTeam.logo}
                      alt={awayTeam.name}
                      className="w-10 h-10 object-contain"
                    />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-bold">{game.awayTeam}</div>
                  <div className="text-xs text-muted-foreground">{awayTeam?.city}</div>
                </div>
                <div className="flex items-center gap-2">
                  {game.awayWinProb && (
                    <span className="text-xs text-muted-foreground">
                      {game.awayWinProb}%
                    </span>
                  )}
                  {pick.winner === game.awayTeam && (
                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              </div>

              {/* Home Team */}
              <div
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                  pick.winner === game.homeTeam
                    ? 'bg-blue-100 border-2 border-blue-500'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
                onClick={() => updatePick(game.id, 'winner', game.homeTeam)}
              >
                <div className="relative">
                  {homeTeam && (
                    <img
                      src={homeTeam.logo}
                      alt={homeTeam.name}
                      className="w-10 h-10 object-contain"
                    />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-bold">{game.homeTeam}</div>
                  <div className="text-xs text-muted-foreground">{homeTeam?.city}</div>
                </div>
                <div className="flex items-center gap-2">
                  {game.homeWinProb && (
                    <span className="text-xs text-muted-foreground">
                      {game.homeWinProb}%
                    </span>
                  )}
                  {pick.winner === game.homeTeam && (
                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardHeader>

          <CardContent className="pt-0">
            {/* Confidence Slider */}
            {pick.winner && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-3"
              >
                <ConfidenceSlider
                  gameId={game.id}
                  value={pick.confidence}
                  onChange={updatePick}
                />

                {/* Confidence Description */}
                <div className="text-xs text-center text-muted-foreground">
                  {pick.confidence <= 3 && "Low confidence - risky pick"}
                  {pick.confidence >= 4 && pick.confidence <= 7 && "Medium confidence - decent pick"}
                  {pick.confidence >= 8 && "High confidence - very sure"}
                </div>
              </motion.div>
            )}

            {/* Error Message */}
            {hasError && (
              <Alert variant="destructive" className="mt-3">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {validationErrors.get(game.id)}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  // Calculate stats
  const totalPicks = Array.from(picks.values()).filter(p => p.winner && p.confidence).length;
  const averageConfidence = totalPicks > 0
    ? (Array.from(picks.values())
        .filter(p => p.confidence)
        .reduce((sum, p) => sum + p.confidence, 0) / totalPicks).toFixed(1)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Target className="w-8 h-8 text-blue-600" />
          NFL Picks
        </h1>
        <p className="text-muted-foreground">
          Select your winners and set confidence levels for each game
        </p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-blue-600">{totalPicks}</div>
          <div className="text-sm text-muted-foreground">Picks Made</div>
        </Card>
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-green-600">{averageConfidence}</div>
          <div className="text-sm text-muted-foreground">Avg Confidence</div>
        </Card>
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-purple-600">{games.length}</div>
          <div className="text-sm text-muted-foreground">Total Games</div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="make-picks">Make Picks</TabsTrigger>
          <TabsTrigger value="my-picks">My Picks</TabsTrigger>
        </TabsList>

        <TabsContent value="make-picks" className="space-y-6">
          {/* Validation Errors */}
          <AnimatePresence>
            {validationErrors.has('confidence_duplicate') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {validationErrors.get('confidence_duplicate')}
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Games Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games.map(game => (
              <GamePickCard key={game.id} game={game} />
            ))}
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <Button
              onClick={handleSubmitPicks}
              disabled={isSubmitting || totalPicks === 0}
              size="lg"
              className="px-8"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Submit Picks ({totalPicks})
                </>
              )}
            </Button>
          </div>

          {/* Submit Status */}
          <AnimatePresence>
            {submitError && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{submitError}</AlertDescription>
                </Alert>
              </motion.div>
            )}

            {submitSuccess && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <Alert className="border-green-500 bg-green-50">
                  <Check className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-700">
                    Picks submitted successfully!
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>
        </TabsContent>

        <TabsContent value="my-picks" className="space-y-6">
          {/* Current Picks Display */}
          {currentPicks.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5" />
                Your Current Picks
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentPicks.map(pick => {
                  const game = games.find(g => g.id === pick.gameId);
                  const team = getTeam(pick.winner);

                  return (
                    <Card key={pick.id} className="p-4">
                      <div className="flex items-center gap-3">
                        {team && (
                          <img
                            src={team.logo}
                            alt={team.name}
                            className="w-8 h-8 object-contain"
                          />
                        )}
                        <div className="flex-1">
                          <div className="font-semibold">{pick.winner}</div>
                          <div className="text-xs text-muted-foreground">
                            vs {game ? (pick.winner === game.homeTeam ? game.awayTeam : game.homeTeam) : 'Unknown'}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 text-yellow-500" />
                            <span className="font-bold">{pick.confidence}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">confidence</div>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Trophy className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Picks Yet</h3>
              <p className="text-muted-foreground mb-4">
                Switch to the "Make Picks" tab to start selecting your winners
              </p>
              <Button onClick={() => setActiveTab('make-picks')}>
                Make Your First Pick
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UserPicks;
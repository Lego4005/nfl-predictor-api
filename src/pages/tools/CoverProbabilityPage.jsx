import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  Target, 
  BarChart3,
  Zap,
  RefreshCw
} from 'lucide-react';
import { useApiCache } from '@/hooks/useCache';

const CoverProbabilityPage = () => {
  const [spread, setSpread] = useState('-3.5');
  const [teamEPA, setTeamEPA] = useState('0.15');
  const [opponentEPA, setOpponentEPA] = useState('-0.12');
  const [homeFieldAdvantage, setHomeFieldAdvantage] = useState('2.5');
  const [results, setResults] = useState(null);
  
  // Use cached data for calculation history
  const [calculationHistory, setCalculationHistory, historyLoading, refreshHistory] = useApiCache(
    '/tools/cover-probability/history', 
    'tools', 
    []
  );

  const calculateCoverProbability = () => {
    const spreadValue = parseFloat(spread) || 0;
    const teamEPAValue = parseFloat(teamEPA) || 0;
    const opponentEPAValue = parseFloat(opponentEPA) || 0;
    const hfaValue = parseFloat(homeFieldAdvantage) || 0;

    // Simplified model for demonstration
    // In a real implementation, this would be more complex
    const expectedMargin = (teamEPAValue - opponentEPAValue) * 10 + hfaValue;
    const standardDeviation = 10; // Assumed standard deviation
    
    // Calculate probability using normal distribution approximation
    const zScore = (expectedMargin - spreadValue) / standardDeviation;
    
    // Approximate cumulative distribution function
    const probability = 0.5 * (1 + Math.erf(zScore / Math.sqrt(2)));
    
    // Expected value calculation
    const ev = probability * 100 - (1 - probability) * 100; // Assuming -110 odds
    
    const newResults = {
      coverProbability: (probability * 100).toFixed(1),
      expectedMargin: expectedMargin.toFixed(1),
      ev: ev.toFixed(2),
      zScore: zScore.toFixed(2)
    };
    
    setResults(newResults);
    
    // Add to calculation history
    const newEntry = {
      id: Date.now(),
      inputs: {
        spread: spreadValue,
        teamEPA: teamEPAValue,
        opponentEPA: opponentEPAValue,
        hfa: hfaValue
      },
      results: newResults,
      timestamp: new Date().toISOString()
    };
    
    setCalculationHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
  };

  // Approximation of error function for normal distribution
  Math.erf = Math.erf || function(x) {
    // Save the sign of x
    var sign = x < 0 ? -1 : 1;
    x = Math.abs(x);
    
    // Constants
    var a1 =  0.254829592;
    var a2 = -0.284496736;
    var a3 =  1.421413741;
    var a4 = -1.453152027;
    var a5 =  1.061405429;
    var p  =  0.3275911;
    
    // A&S formula 7.1.26
    var t = 1.0/(1.0 + p*x);
    var y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*Math.exp(-x*x);
    
    return sign*y;
  };

  // Clear history
  const clearHistory = () => {
    setCalculationHistory([]);
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              Cover Probability Calculator
            </h1>
            <p className="dashboard-muted">
              Calculate the probability of a team covering the spread based on EPA metrics
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              onClick={refreshHistory}
              className="flex items-center gap-2 px-3 py-2 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg hover:opacity-80 transition-opacity"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="text-sm">Refresh</span>
            </Button>
            
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-green-400" />
              <span className="text-sm dashboard-muted">Betting Tool</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <BarChart3 className="w-5 h-5" />
                  Input Parameters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label className="dashboard-text mb-2 block">Point Spread</Label>
                  <Input
                    type="text"
                    value={spread}
                    onChange={(e) => setSpread(e.target.value)}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="-3.5"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Negative for favorites, positive for underdogs
                  </p>
                </div>

                <div>
                  <Label className="dashboard-text mb-2 block">Team EPA</Label>
                  <Input
                    type="text"
                    value={teamEPA}
                    onChange={(e) => setTeamEPA(e.target.value)}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="0.15"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Expected Points Added per play
                  </p>
                </div>

                <div>
                  <Label className="dashboard-text mb-2 block">Opponent EPA</Label>
                  <Input
                    type="text"
                    value={opponentEPA}
                    onChange={(e) => setOpponentEPA(e.target.value)}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="-0.12"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Opponent's defensive EPA allowed
                  </p>
                </div>

                <div>
                  <Label className="dashboard-text mb-2 block">Home Field Advantage</Label>
                  <Input
                    type="text"
                    value={homeFieldAdvantage}
                    onChange={(e) => setHomeFieldAdvantage(e.target.value)}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="2.5"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Points advantage for home team
                  </p>
                </div>

                <Button 
                  onClick={calculateCoverProbability}
                  className="w-full dashboard-button-primary"
                >
                  Calculate Cover Probability
                </Button>
              </CardContent>
            </Card>

            {/* Quick Reference */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="dashboard-text">How It Works</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm dashboard-muted">
                  <p>
                    This calculator uses EPA (Expected Points Added) metrics to estimate the probability of a team covering the spread.
                  </p>
                  <p>
                    The model considers team performance, opponent strength, and home field advantage to project the expected margin of victory.
                  </p>
                  <p>
                    A higher cover probability indicates a better betting opportunity.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <TrendingUp className="w-5 h-5" />
                  Analysis Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                {results ? (
                  <div className="space-y-6">
                    {/* Main Results */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">Cover Probability</div>
                        <div className="text-3xl font-bold text-green-400">
                          {results.coverProbability}%
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Chance of covering the spread
                        </div>
                      </div>
                      
                      <div className="p-4 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">Expected Margin</div>
                        <div className="text-3xl font-bold text-blue-400">
                          {results.expectedMargin}
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Projected point differential
                        </div>
                      </div>
                      
                      <div className="p-4 bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">Expected Value</div>
                        <div className={`text-3xl font-bold ${parseFloat(results.ev) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ${results.ev}
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Per $100 bet at -110 odds
                        </div>
                      </div>
                      
                      <div className="p-4 bg-gradient-to-br from-yellow-900/20 to-orange-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">Z-Score</div>
                        <div className="text-3xl font-bold text-yellow-400">
                          {results.zScore}
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Standard deviations from mean
                        </div>
                      </div>
                    </div>

                    {/* Interpretation */}
                    <div className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                      <h3 className="font-semibold dashboard-text mb-2">Interpretation</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="dashboard-muted">Cover Probability:</div>
                          <div className="dashboard-text">
                            {parseFloat(results.coverProbability) > 60 ? 'High probability of covering' : 
                             parseFloat(results.coverProbability) > 50 ? 'Slight edge to cover' : 
                             'Underdog to cover the spread'}
                          </div>
                        </div>
                        <div>
                          <div className="dashboard-muted">Expected Value:</div>
                          <div className={`font-medium ${parseFloat(results.ev) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {parseFloat(results.ev) > 0 ? 'Positive expected value (+EV)' : 'Negative expected value (-EV)'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 dashboard-muted">
                    <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Enter parameters and click calculate</p>
                    <p className="text-sm mt-1">Results will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Calculation History */}
            <Card className="dashboard-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 dashboard-text">
                    <BarChart3 className="w-5 h-5" />
                    Recent Calculations
                  </CardTitle>
                  <Button 
                    onClick={clearHistory}
                    variant="outline" 
                    size="sm"
                    className="text-xs border-gray-700 dashboard-text"
                  >
                    Clear
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {calculationHistory.length === 0 ? (
                  <div className="text-center py-8 dashboard-muted">
                    <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No calculation history yet</p>
                    <p className="text-xs mt-1">Perform calculations to see history</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {calculationHistory.map((entry) => (
                      <div key={entry.id} className="p-3 bg-[hsl(var(--dashboard-surface))] rounded border border-gray-700">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-medium dashboard-text">
                            {entry.inputs.spread > 0 ? '+' : ''}{entry.inputs.spread} spread
                          </div>
                          <div className="text-xs dashboard-muted">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <div className="dashboard-muted">Cover Prob</div>
                            <div className="dashboard-text">{entry.results.coverProbability}%</div>
                          </div>
                          <div>
                            <div className="dashboard-muted">Expected EV</div>
                            <div className={`font-medium ${parseFloat(entry.results.ev) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              ${entry.results.ev}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoverProbabilityPage;
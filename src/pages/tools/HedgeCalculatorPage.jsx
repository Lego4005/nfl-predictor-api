import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { 
  Calculator, 
  TrendingUp, 
  TrendingDown,
  Minus,
  Zap,
  RefreshCw
} from 'lucide-react';
import { useApiCache } from '@/hooks/useCache';

const HedgeCalculatorPage = () => {
  const [originalBet, setOriginalBet] = useState({
    odds: '-110',
    stake: '100'
  });
  
  const [hedgeOdds, setHedgeOdds] = useState('-110');
  const [strategy, setStrategy] = useState('break_even');
  const [results, setResults] = useState(null);
  
  // Use cached data for calculation history
  const [calculationHistory, setCalculationHistory, historyLoading, refreshHistory] = useApiCache(
    '/tools/hedge-calculator/history', 
    'tools', 
    []
  );

  const calculateHedge = () => {
    const originalOdds = parseFloat(originalBet.odds) || -110;
    const originalStake = parseFloat(originalBet.stake) || 100;
    const hedgeOddsValue = parseFloat(hedgeOdds) || -110;

    // Calculate original bet payout
    const originalPayout = originalOdds > 0 
      ? (originalOdds / 100) * originalStake 
      : (100 / Math.abs(originalOdds)) * originalStake;
    
    const originalTotalReturn = originalStake + originalPayout;

    let hedgeStake, profitIfOriginalWins, profitIfHedgeWins;

    switch (strategy) {
      case 'break_even':
        // Calculate stake needed to break even if hedge wins
        hedgeStake = originalTotalReturn / (hedgeOddsValue > 0 
          ? (hedgeOddsValue / 100 + 1) 
          : (100 / Math.abs(hedgeOddsValue) + 1));
        profitIfOriginalWins = originalPayout - hedgeStake;
        profitIfHedgeWins = originalTotalReturn - hedgeStake;
        break;
        
      case 'equal_profit':
        // Calculate stake for equal profit regardless of outcome
        hedgeStake = (originalPayout - originalStake) / (hedgeOddsValue > 0 
          ? (hedgeOddsValue / 100) 
          : (100 / Math.abs(hedgeOddsValue)));
        profitIfOriginalWins = originalPayout - hedgeStake;
        profitIfHedgeWins = (hedgeOddsValue > 0 
          ? (hedgeOddsValue / 100) * hedgeStake 
          : (100 / Math.abs(hedgeOddsValue)) * hedgeStake) - originalStake;
        break;
        
      case 'no_hedge':
      default:
        hedgeStake = 0;
        profitIfOriginalWins = originalPayout;
        profitIfHedgeWins = -originalStake;
        break;
    }

    const newResults = {
      hedgeStake: hedgeStake.toFixed(2),
      profitIfOriginalWins: profitIfOriginalWins.toFixed(2),
      profitIfHedgeWins: profitIfHedgeWins.toFixed(2),
      originalPayout: originalPayout.toFixed(2),
      originalTotalReturn: originalTotalReturn.toFixed(2)
    };
    
    setResults(newResults);
    
    // Add to calculation history
    const newEntry = {
      id: Date.now(),
      inputs: {
        originalBet,
        hedgeOdds: hedgeOddsValue,
        strategy
      },
      results: newResults,
      timestamp: new Date().toISOString()
    };
    
    setCalculationHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
  };

  const getStrategyDescription = (strategy) => {
    switch (strategy) {
      case 'break_even':
        return 'Guarantee the same profit regardless of outcome';
      case 'equal_profit':
        return 'Maximize minimum profit across both outcomes';
      case 'no_hedge':
        return 'No hedge - take full risk on original bet';
      default:
        return '';
    }
  };

  // Clear history
  const clearHistory = () => {
    setCalculationHistory([]);
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              Hedge Calculator
            </h1>
            <p className="dashboard-muted">
              Calculate optimal hedge amounts to minimize risk or maximize profit
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
              <Calculator className="w-5 h-5 text-purple-400" />
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
                  <Zap className="w-5 h-5" />
                  Original Bet
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="dashboard-text mb-2 block">Odds</Label>
                  <Input
                    type="text"
                    value={originalBet.odds}
                    onChange={(e) => setOriginalBet({...originalBet, odds: e.target.value})}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="-110"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    American odds (e.g., -110, +150)
                  </p>
                </div>

                <div>
                  <Label className="dashboard-text mb-2 block">Stake ($)</Label>
                  <Input
                    type="text"
                    value={originalBet.stake}
                    onChange={(e) => setOriginalBet({...originalBet, stake: e.target.value})}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="100"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Amount wagered on original bet
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <TrendingDown className="w-5 h-5" />
                  Hedge Bet
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div>
                  <Label className="dashboard-text mb-2 block">Hedge Odds</Label>
                  <Input
                    type="text"
                    value={hedgeOdds}
                    onChange={(e) => setHedgeOdds(e.target.value)}
                    className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text"
                    placeholder="-110"
                  />
                  <p className="text-xs dashboard-muted mt-1">
                    Odds for opposite outcome
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <Calculator className="w-5 h-5" />
                  Strategy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="strategy"
                      value="no_hedge"
                      checked={strategy === 'no_hedge'}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="mr-2"
                    />
                    <span className="dashboard-text">No Hedge</span>
                  </label>
                  <p className="text-xs dashboard-muted ml-6">
                    Take full risk on original bet
                  </p>
                </div>
                
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="strategy"
                      value="break_even"
                      checked={strategy === 'break_even'}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="mr-2"
                    />
                    <span className="dashboard-text">Break Even</span>
                  </label>
                  <p className="text-xs dashboard-muted ml-6">
                    Guarantee same profit regardless of outcome
                  </p>
                </div>
                
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="strategy"
                      value="equal_profit"
                      checked={strategy === 'equal_profit'}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="mr-2"
                    />
                    <span className="dashboard-text">Equal Profit</span>
                  </label>
                  <p className="text-xs dashboard-muted ml-6">
                    Maximize minimum profit across outcomes
                  </p>
                </div>
              </CardContent>
            </Card>

            <Button 
              onClick={calculateHedge}
              className="w-full dashboard-button-primary"
            >
              Calculate Hedge
            </Button>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <TrendingUp className="w-5 h-5" />
                  Hedge Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                {results ? (
                  <div className="space-y-6">
                    {/* Strategy Summary */}
                    <div className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold dashboard-text capitalize">
                            {strategy.replace('_', ' ')} Strategy
                          </h3>
                          <p className="text-sm dashboard-muted">
                            {getStrategyDescription(strategy)}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm dashboard-muted">Hedge Stake</div>
                          <div className="text-xl font-bold text-purple-400">
                            ${results.hedgeStake}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Profit Comparison */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">If Original Bet Wins</div>
                        <div className={`text-2xl font-bold ${parseFloat(results.profitIfOriginalWins) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ${results.profitIfOriginalWins}
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Original payout: ${results.originalPayout}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 rounded-lg">
                        <div className="text-sm dashboard-muted mb-1">If Hedge Bet Wins</div>
                        <div className={`text-2xl font-bold ${parseFloat(results.profitIfHedgeWins) >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                          ${results.profitIfHedgeWins}
                        </div>
                        <div className="text-xs dashboard-muted mt-1">
                          Hedge payout: ${parseFloat(results.hedgeStake) > 0 ? (parseFloat(hedgeOdds) > 0 ? (parseFloat(hedgeOdds) / 100 * parseFloat(results.hedgeStake)).toFixed(2) : (100 / Math.abs(parseFloat(hedgeOdds)) * parseFloat(results.hedgeStake)).toFixed(2)) : '0.00'}
                        </div>
                      </div>
                    </div>

                    {/* Risk Assessment */}
                    <div className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                      <h3 className="font-semibold dashboard-text mb-3">Risk Assessment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="dashboard-muted">Maximum Loss</div>
                          <div className="dashboard-text">
                            ${Math.min(parseFloat(results.profitIfOriginalWins), parseFloat(results.profitIfHedgeWins)).toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="dashboard-muted">Maximum Profit</div>
                          <div className="dashboard-text">
                            ${Math.max(parseFloat(results.profitIfOriginalWins), parseFloat(results.profitIfHedgeWins)).toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="dashboard-muted">Risk Reduction</div>
                          <div className="dashboard-text">
                            {strategy === 'no_hedge' ? '0%' : 
                             Math.round((1 - Math.abs(parseFloat(results.profitIfOriginalWins) - parseFloat(results.profitIfHedgeWins)) / parseFloat(results.originalPayout)) * 100)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 dashboard-muted">
                    <Calculator className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Enter parameters and click calculate</p>
                    <p className="text-sm mt-1">Hedge analysis will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Calculation History */}
            <Card className="dashboard-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 dashboard-text">
                    <Calculator className="w-5 h-5" />
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
                    <Calculator className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No calculation history yet</p>
                    <p className="text-xs mt-1">Perform calculations to see history</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {calculationHistory.map((entry) => (
                      <div key={entry.id} className="p-3 bg-[hsl(var(--dashboard-surface))] rounded border border-gray-700">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-medium dashboard-text capitalize">
                            {entry.inputs.strategy.replace('_', ' ')}
                          </div>
                          <div className="text-xs dashboard-muted">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <div className="dashboard-muted">Original</div>
                            <div className="dashboard-text">${entry.inputs.originalBet.stake} @ {entry.inputs.originalBet.odds}</div>
                          </div>
                          <div>
                            <div className="dashboard-muted">Hedge</div>
                            <div className="dashboard-text">${entry.results.hedgeStake} @ {entry.inputs.hedgeOdds}</div>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-700 text-xs">
                          <div className="flex justify-between">
                            <span className="dashboard-muted">Profit Range:</span>
                            <span className="dashboard-text">
                              ${Math.min(parseFloat(entry.results.profitIfOriginalWins), parseFloat(entry.results.profitIfHedgeWins)).toFixed(2)} to 
                              ${Math.max(parseFloat(entry.results.profitIfOriginalWins), parseFloat(entry.results.profitIfHedgeWins)).toFixed(2)}
                            </span>
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

export default HedgeCalculatorPage;
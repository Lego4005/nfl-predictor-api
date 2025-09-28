import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { 
  Calculator, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  RefreshCw
} from 'lucide-react';
import { useApiCache } from '@/hooks/useCache';

// Utility functions for odds conversion
const americanToImplied = (odds) => {
  if (odds > 0) {
    return 100 / (odds + 100);
  } else {
    return -odds / (-odds + 100);
  }
};

const impliedToAmerican = (p) => {
  if (p <= 0 || p >= 1) return Infinity;
  if (p >= 0.5) {
    return Math.round((-p * 100) / (1 - p));
  } else {
    return Math.round(((1 - p) * 100) / p);
  }
};

const decimalToAmerican = (odds) => {
  if (odds >= 2.0) {
    return Math.round((odds - 1) * 100);
  } else {
    return Math.round(-100 / (odds - 1));
  }
};

const americanToDecimal = (odds) => {
  if (odds > 0) {
    return odds / 100 + 1;
  } else {
    return 100 / Math.abs(odds) + 1;
  }
};

const fractionalToDecimal = (fraction) => {
  if (fraction.includes('/')) {
    const [numerator, denominator] = fraction.split('/').map(Number);
    if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
      return numerator / denominator + 1;
    }
  }
  return null;
};

const decimalToFractional = (decimal) => {
  if (decimal <= 1) return null;
  
  // Convert to fraction with precision
  const precision = 10000;
  const numerator = Math.round((decimal - 1) * precision);
  const denominator = precision;
  
  // Simplify fraction
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  const divisor = gcd(numerator, denominator);
  
  return `${numerator / divisor}/${denominator / divisor}`;
};

const OddsConverterPage = () => {
  // Use cached data for recent conversions
  const [conversionHistory, setConversionHistory, historyLoading, refreshHistory] = useApiCache(
    '/tools/odds-converter/history', 
    'tools', 
    []
  );
  
  const [americanOdds, setAmericanOdds] = useState('-110');
  const [decimalOdds, setDecimalOdds] = useState('1.91');
  const [fractionalOdds, setFractionalOdds] = useState('10/11');
  const [impliedProbability, setImpliedProbability] = useState('52.38');

  const updateFromAmerican = useCallback((value) => {
    const odds = parseFloat(value);
    if (!isNaN(odds)) {
      setAmericanOdds(value);
      const decimal = americanToDecimal(odds);
      setDecimalOdds(decimal.toFixed(2));
      const fractional = decimalToFractional(decimal);
      if (fractional) setFractionalOdds(fractional);
      const implied = americanToImplied(odds) * 100;
      setImpliedProbability(implied.toFixed(2));
      
      // Add to conversion history
      const newEntry = {
        id: Date.now(),
        american: value,
        decimal: decimal.toFixed(2),
        fractional: fractional || 'N/A',
        implied: implied.toFixed(2),
        timestamp: new Date().toISOString()
      };
      
      setConversionHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
    }
  }, [setConversionHistory]);

  const updateFromDecimal = useCallback((value) => {
    const odds = parseFloat(value);
    if (!isNaN(odds) && odds > 1) {
      setDecimalOdds(value);
      const american = decimalToAmerican(odds);
      setAmericanOdds(american.toString());
      const fractional = decimalToFractional(odds);
      if (fractional) setFractionalOdds(fractional);
      const implied = (1 / odds) * 100;
      setImpliedProbability(implied.toFixed(2));
      
      // Add to conversion history
      const newEntry = {
        id: Date.now(),
        american: american.toString(),
        decimal: value,
        fractional: fractional || 'N/A',
        implied: implied.toFixed(2),
        timestamp: new Date().toISOString()
      };
      
      setConversionHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
    }
  }, [setConversionHistory]);

  const updateFromFractional = useCallback((value) => {
    const decimal = fractionalToDecimal(value);
    if (decimal !== null) {
      setFractionalOdds(value);
      const american = decimalToAmerican(decimal);
      setAmericanOdds(american.toString());
      setDecimalOdds(decimal.toFixed(2));
      const implied = (1 / decimal) * 100;
      setImpliedProbability(implied.toFixed(2));
      
      // Add to conversion history
      const newEntry = {
        id: Date.now(),
        american: american.toString(),
        decimal: decimal.toFixed(2),
        fractional: value,
        implied: implied.toFixed(2),
        timestamp: new Date().toISOString()
      };
      
      setConversionHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
    }
  }, [setConversionHistory]);

  const updateFromImplied = useCallback((value) => {
    const prob = parseFloat(value);
    if (!isNaN(prob) && prob > 0 && prob < 100) {
      setImpliedProbability(value);
      const american = impliedToAmerican(prob / 100);
      setAmericanOdds(american.toString());
      const decimal = americanToDecimal(american);
      setDecimalOdds(decimal.toFixed(2));
      const fractional = decimalToFractional(decimal);
      if (fractional) setFractionalOdds(fractional);
      
      // Add to conversion history
      const newEntry = {
        id: Date.now(),
        american: american.toString(),
        decimal: decimal.toFixed(2),
        fractional: fractional || 'N/A',
        implied: value,
        timestamp: new Date().toISOString()
      };
      
      setConversionHistory(prev => [newEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
    }
  }, [setConversionHistory]);

  // Clear history
  const clearHistory = () => {
    setConversionHistory([]);
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              Odds Converter
            </h1>
            <p className="dashboard-muted">
              Convert between different odds formats and calculate implied probabilities
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
              <Calculator className="w-5 h-5 text-blue-400" />
              <span className="text-sm dashboard-muted">Betting Tool</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Converter Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <DollarSign className="w-5 h-5" />
                  Odds Conversion Calculator
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Input Section */}
                  <div className="space-y-6">
                    <div>
                      <Label className="dashboard-text mb-2 block">American Odds</Label>
                      <div className="relative">
                        <Input
                          type="text"
                          value={americanOdds}
                          onChange={(e) => updateFromAmerican(e.target.value)}
                          className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text pl-10"
                          placeholder="-110"
                        />
                        <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 dashboard-muted" />
                      </div>
                      <p className="text-xs dashboard-muted mt-1">
                        Favorites: -110, Underdogs: +150
                      </p>
                    </div>

                    <div>
                      <Label className="dashboard-text mb-2 block">Decimal Odds</Label>
                      <div className="relative">
                        <Input
                          type="text"
                          value={decimalOdds}
                          onChange={(e) => updateFromDecimal(e.target.value)}
                          className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text pl-10"
                          placeholder="1.91"
                        />
                        <TrendingUp className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 dashboard-muted" />
                      </div>
                      <p className="text-xs dashboard-muted mt-1">
                        European format (e.g., 1.91, 2.50)
                      </p>
                    </div>

                    <div>
                      <Label className="dashboard-text mb-2 block">Fractional Odds</Label>
                      <div className="relative">
                        <Input
                          type="text"
                          value={fractionalOdds}
                          onChange={(e) => updateFromFractional(e.target.value)}
                          className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text pl-10"
                          placeholder="10/11"
                        />
                        <TrendingDown className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 dashboard-muted" />
                      </div>
                      <p className="text-xs dashboard-muted mt-1">
                        UK format (e.g., 5/2, 3/1)
                      </p>
                    </div>

                    <div>
                      <Label className="dashboard-text mb-2 block">Implied Probability</Label>
                      <div className="relative">
                        <Input
                          type="text"
                          value={impliedProbability}
                          onChange={(e) => updateFromImplied(e.target.value)}
                          className="bg-[hsl(var(--dashboard-surface))] border-gray-700 dashboard-text pl-10"
                          placeholder="52.38"
                        />
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 dashboard-muted">%</span>
                      </div>
                      <p className="text-xs dashboard-muted mt-1">
                        Chance of winning (0-100%)
                      </p>
                    </div>
                  </div>

                  {/* Conversion Results */}
                  <div className="space-y-4">
                    <div className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                      <h3 className="font-semibold dashboard-text mb-3">Conversion Results</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="dashboard-muted">American Odds</span>
                          <span className="font-medium dashboard-text">{americanOdds}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="dashboard-muted">Decimal Odds</span>
                          <span className="font-medium dashboard-text">{decimalOdds}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="dashboard-muted">Fractional Odds</span>
                          <span className="font-medium dashboard-text">{fractionalOdds}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="dashboard-muted">Implied Probability</span>
                          <span className="font-medium dashboard-text">{impliedProbability}%</span>
                        </div>
                        <div className="flex justify-between pt-2 border-t border-gray-700">
                          <span className="dashboard-muted">Payout (on $100 bet)</span>
                          <span className="font-medium dashboard-text">
                            ${americanOdds.startsWith('-') ? 
                              (100 / Math.abs(parseFloat(americanOdds)) * 100 + 100).toFixed(2) : 
                              (parseFloat(americanOdds) + 100).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-lg">
                      <h3 className="font-semibold dashboard-text mb-2">How to Use</h3>
                      <ul className="text-sm space-y-1 dashboard-muted">
                        <li>• Enter any odds format to convert</li>
                        <li>• Results update automatically</li>
                        <li>• History saves your recent conversions</li>
                        <li>• Use for comparing betting opportunities</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* History Section */}
          <div className="space-y-6">
            <Card className="dashboard-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 dashboard-text">
                    <Calculator className="w-5 h-5" />
                    Conversion History
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
                {conversionHistory.length === 0 ? (
                  <div className="text-center py-8 dashboard-muted">
                    <Calculator className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No conversion history yet</p>
                    <p className="text-xs mt-1">Start converting odds to see history</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {conversionHistory.map((entry) => (
                      <div key={entry.id} className="p-3 bg-[hsl(var(--dashboard-surface))] rounded border border-gray-700">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-medium dashboard-text">{entry.american}</div>
                          <div className="text-xs dashboard-muted">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <div className="dashboard-muted">Decimal</div>
                            <div className="dashboard-text">{entry.decimal}</div>
                          </div>
                          <div>
                            <div className="dashboard-muted">Fraction</div>
                            <div className="dashboard-text">{entry.fractional}</div>
                          </div>
                          <div>
                            <div className="dashboard-muted">Implied</div>
                            <div className="dashboard-text">{entry.implied}%</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Reference */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="dashboard-text">Quick Reference</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <h4 className="font-medium dashboard-text mb-1">American Odds</h4>
                    <p className="text-xs dashboard-muted">
                      Favorites: Negative numbers (e.g., -150)<br/>
                      Underdogs: Positive numbers (e.g., +130)
                    </p>
                  </div>
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <h4 className="font-medium dashboard-text mb-1">Decimal Odds</h4>
                    <p className="text-xs dashboard-muted">
                      European format<br/>
                      Payout = Stake × Decimal Odds
                    </p>
                  </div>
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <h4 className="font-medium dashboard-text mb-1">Fractional Odds</h4>
                    <p className="text-xs dashboard-muted">
                      UK format<br/>
                      Payout = Stake × (Numerator/Denominator)
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OddsConverterPage;
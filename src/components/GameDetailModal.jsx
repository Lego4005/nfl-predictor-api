import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { getTeam } from '../data/nflTeams';
import {
  Activity, TrendingUp, Users, Cloud, DollarSign,
  AlertCircle, Thermometer, Wind, Droplets, Trophy,
  ArrowUp, ArrowDown, Shield, Zap, Heart
} from 'lucide-react';

const GameDetailModal = ({ game, isOpen, onClose }) => {
  const homeTeam = getTeam(game?.homeTeam);
  const awayTeam = getTeam(game?.awayTeam);

  if (!game) return null;

  // Mock data for demonstration
  const mockData = {
    confidence: 78,
    keyFactors: [
      { factor: 'Home Advantage', impact: '+3%', positive: true },
      { factor: 'Recent Form', impact: '+5%', positive: true },
      { factor: 'Key Injuries', impact: '-2%', positive: false }
    ],
    h2hRecord: { home: 7, away: 3 },
    injuries: {
      home: [
        { player: 'Star RB', status: 'Questionable', impact: -5 },
        { player: 'WR2', status: 'Out', impact: -2 }
      ],
      away: [
        { player: 'CB1', status: 'Doubtful', impact: -3 }
      ]
    },
    weather: {
      temp: 45,
      wind: 15,
      precipitation: 20,
      condition: 'Partly Cloudy'
    },
    betting: {
      lineMovement: [
        { time: '7d ago', line: -3 },
        { time: '3d ago', line: -3.5 },
        { time: '1d ago', line: -4 },
        { time: 'Current', line: -3.5 }
      ],
      publicMoney: 65,
      sharpMoney: 35
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog open={isOpen} onOpenChange={onClose}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl">
            {/* Header with team gradients */}
            <div className="h-2 flex rounded-t-lg overflow-hidden">
              <div className="flex-1" style={{ background: awayTeam?.gradient }} />
              <div className="flex-1" style={{ background: homeTeam?.gradient }} />
            </div>

            <DialogHeader className="pb-4">
              <DialogTitle className="text-2xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {awayTeam && (
                      <img src={awayTeam.logo} alt={awayTeam.name} className="w-12 h-12" />
                    )}
                    <span>{game.awayTeam}</span>
                    <span className="text-muted-foreground">@</span>
                    <span>{game.homeTeam}</span>
                    {homeTeam && (
                      <img src={homeTeam.logo} alt={homeTeam.name} className="w-12 h-12" />
                    )}
                  </div>
                  <Badge variant="outline">
                    {new Date(game.startTime).toLocaleDateString([], {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit'
                    })}
                  </Badge>
                </div>
              </DialogTitle>
            </DialogHeader>

            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid grid-cols-5 w-full">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="matchup">Matchup</TabsTrigger>
                <TabsTrigger value="injuries">Injuries</TabsTrigger>
                <TabsTrigger value="weather">Weather</TabsTrigger>
                <TabsTrigger value="betting">Betting</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">ML Prediction Confidence</h3>
                      <Badge className="bg-green-600 text-white">
                        {mockData.confidence}% {homeTeam?.abbreviation} Win
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Progress value={mockData.confidence} className="h-3 mb-4" />

                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-muted-foreground">Key Factors</h4>
                      {mockData.keyFactors.map((factor, i) => (
                        <div key={i} className="flex items-center justify-between py-1">
                          <span className="text-sm">{factor.factor}</span>
                          <Badge variant={factor.positive ? "default" : "destructive"}>
                            {factor.impact}
                          </Badge>
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">{game.awayWinProb || 45}%</div>
                        <div className="text-xs text-muted-foreground">{awayTeam?.name} Win Prob</div>
                      </div>
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">{game.homeWinProb || 55}%</div>
                        <div className="text-xs text-muted-foreground">{homeTeam?.name} Win Prob</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Matchup Analysis Tab */}
              <TabsContent value="matchup" className="space-y-4">
                <Card>
                  <CardHeader>
                    <h3 className="font-semibold">Head-to-Head History</h3>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-center">
                        <div className="text-3xl font-bold">{mockData.h2hRecord.away}</div>
                        <div className="text-sm text-muted-foreground">{awayTeam?.name} Wins</div>
                      </div>
                      <div className="text-muted-foreground">Last 10 Games</div>
                      <div className="text-center">
                        <div className="text-3xl font-bold">{mockData.h2hRecord.home}</div>
                        <div className="text-sm text-muted-foreground">{homeTeam?.name} Wins</div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Offensive Ranking</span>
                        <div className="flex gap-4">
                          <Badge variant="outline">#{Math.floor(Math.random() * 10 + 1)}</Badge>
                          <Badge variant="outline">#{Math.floor(Math.random() * 10 + 1)}</Badge>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Defensive Ranking</span>
                        <div className="flex gap-4">
                          <Badge variant="outline">#{Math.floor(Math.random() * 10 + 1)}</Badge>
                          <Badge variant="outline">#{Math.floor(Math.random() * 10 + 1)}</Badge>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Points Per Game</span>
                        <div className="flex gap-4">
                          <span className="font-medium">24.3</span>
                          <span className="font-medium">27.1</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Injuries Tab */}
              <TabsContent value="injuries" className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <h3 className="font-semibold flex items-center gap-2">
                        {awayTeam?.name} Injuries
                        <Heart className="w-4 h-4 text-red-500" />
                      </h3>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {mockData.injuries.away.map((injury, i) => (
                        <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                          <div>
                            <div className="font-medium">{injury.player}</div>
                            <Badge variant="outline" className="text-xs">
                              {injury.status}
                            </Badge>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-red-500">
                              {injury.impact}% Impact
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <h3 className="font-semibold flex items-center gap-2">
                        {homeTeam?.name} Injuries
                        <Heart className="w-4 h-4 text-red-500" />
                      </h3>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {mockData.injuries.home.map((injury, i) => (
                        <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                          <div>
                            <div className="font-medium">{injury.player}</div>
                            <Badge variant="outline" className="text-xs">
                              {injury.status}
                            </Badge>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-red-500">
                              {injury.impact}% Impact
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Weather Tab */}
              <TabsContent value="weather" className="space-y-4">
                <Card>
                  <CardHeader>
                    <h3 className="font-semibold">Game Day Conditions</h3>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Thermometer className="w-8 h-8 mx-auto mb-2 text-orange-500" />
                        <div className="text-2xl font-bold">{mockData.weather.temp}°F</div>
                        <div className="text-xs text-muted-foreground">Temperature</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Wind className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                        <div className="text-2xl font-bold">{mockData.weather.wind} mph</div>
                        <div className="text-xs text-muted-foreground">Wind Speed</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Droplets className="w-8 h-8 mx-auto mb-2 text-cyan-500" />
                        <div className="text-2xl font-bold">{mockData.weather.precipitation}%</div>
                        <div className="text-xs text-muted-foreground">Precipitation</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <Cloud className="w-8 h-8 mx-auto mb-2 text-gray-500" />
                        <div className="text-lg font-bold">{mockData.weather.condition}</div>
                        <div className="text-xs text-muted-foreground">Conditions</div>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm">
                        <strong>Historical Performance:</strong> {homeTeam?.name} is 8-2 in games with
                        wind speeds over 10mph. The Under has hit 73% when wind exceeds 15mph at this stadium.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Betting Intelligence Tab */}
              <TabsContent value="betting" className="space-y-4">
                <Card>
                  <CardHeader>
                    <h3 className="font-semibold">Line Movement</h3>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {mockData.betting.lineMovement.map((movement, i) => (
                        <div key={i} className="flex items-center justify-between py-2">
                          <span className="text-sm text-muted-foreground">{movement.time}</span>
                          <Badge variant={i === mockData.betting.lineMovement.length - 1 ? "default" : "outline"}>
                            {homeTeam?.abbreviation} {movement.line}
                          </Badge>
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-6">
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Public Money</span>
                          <span className="font-bold">{mockData.betting.publicMoney}%</span>
                        </div>
                        <Progress value={mockData.betting.publicMoney} className="h-2" />
                      </div>
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">Sharp Money</span>
                          <span className="font-bold">{mockData.betting.sharpMoney}%</span>
                        </div>
                        <Progress value={mockData.betting.sharpMoney} className="h-2" />
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <p className="text-sm">
                        <strong>Value Alert:</strong> Line moved from {homeTeam?.abbreviation} -4 to -3.5
                        despite 65% of public money on {homeTeam?.name}. Sharp money appears to be on {awayTeam?.name}.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  );
};

export default GameDetailModal;
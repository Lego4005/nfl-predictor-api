import React, { useState } from 'react';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

function SimpleDashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data for testing
  const mockGames = [
    {
      id: '1',
      homeTeam: 'Chiefs',
      awayTeam: 'Bills',
      homeScore: 24,
      awayScore: 21,
      status: 'live',
      quarter: 3,
      time: '5:43'
    },
    {
      id: '2',
      homeTeam: 'Eagles',
      awayTeam: 'Cowboys',
      homeScore: 17,
      awayScore: 14,
      status: 'live',
      quarter: 2,
      time: '2:15'
    },
    {
      id: '3',
      homeTeam: '49ers',
      awayTeam: 'Rams',
      homeScore: 0,
      awayScore: 0,
      status: 'scheduled',
      quarter: 0,
      time: '4:25 PM'
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground p-4">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">NFL Prediction Dashboard</h1>
          <Badge variant="default">Live</Badge>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="live">Live Games</TabsTrigger>
            <TabsTrigger value="predictions">Predictions</TabsTrigger>
            <TabsTrigger value="betting">Betting</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockGames.map(game => (
                <Card key={game.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">
                        {game.awayTeam} @ {game.homeTeam}
                      </span>
                      <Badge variant={game.status === 'live' ? 'default' : 'secondary'}>
                        {game.status.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {game.awayScore} - {game.homeScore}
                    </div>
                    {game.status === 'live' && (
                      <div className="text-sm text-muted-foreground mt-2">
                        Q{game.quarter} · {game.time}
                      </div>
                    )}
                    {game.status === 'scheduled' && (
                      <div className="text-sm text-muted-foreground mt-2">
                        Starts at {game.time}
                      </div>
                    )}
                  </CardContent>
                  <CardFooter>
                    <Button variant="outline" size="sm" className="w-full">
                      View Details
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="live" className="mt-6">
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold mb-2">Live Games</h2>
              <p className="text-muted-foreground">
                {mockGames.filter(g => g.status === 'live').length} games currently in progress
              </p>
            </div>
          </TabsContent>

          <TabsContent value="predictions" className="mt-6">
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold mb-2">AI Predictions</h2>
              <p className="text-muted-foreground">Advanced ML predictions coming soon</p>
            </div>
          </TabsContent>

          <TabsContent value="betting" className="mt-6">
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold mb-2">Betting Insights</h2>
              <p className="text-muted-foreground">Odds comparison and value bets</p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default SimpleDashboard;
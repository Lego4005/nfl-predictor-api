import React from "react";
import { TabsList, TabsTrigger } from "@/components/ui/tabs";

export function DesktopTabsList() {
  return (
    <TabsList className="hidden lg:grid w-full grid-cols-8">
      <TabsTrigger value="overview" className="touch-friendly">
        Overview
      </TabsTrigger>
      <TabsTrigger value="live" className="touch-friendly">
        Live
      </TabsTrigger>
      <TabsTrigger value="analytics" className="touch-friendly">
        Analytics
      </TabsTrigger>
      <TabsTrigger value="predictions" className="touch-friendly">
        Predictions
      </TabsTrigger>
      <TabsTrigger value="players" className="touch-friendly">
        Players
      </TabsTrigger>
      <TabsTrigger value="betting" className="touch-friendly">
        Betting
      </TabsTrigger>
      <TabsTrigger value="leaderboard" className="touch-friendly">
        Leaderboard
      </TabsTrigger>
      <TabsTrigger value="health" className="touch-friendly">
        Health
      </TabsTrigger>
    </TabsList>
  );
}

export function MobileTabsList() {
  return (
    <div className="lg:hidden mb-4 overflow-x-auto scrollbar-hide">
      <TabsList className="flex w-max min-w-full">
        <TabsTrigger
          value="overview"
          className="touch-friendly whitespace-nowrap"
        >
          Overview
        </TabsTrigger>
        <TabsTrigger
          value="live"
          className="touch-friendly whitespace-nowrap"
        >
          Live
        </TabsTrigger>
        <TabsTrigger
          value="analytics"
          className="touch-friendly whitespace-nowrap"
        >
          Analytics
        </TabsTrigger>
        <TabsTrigger
          value="predictions"
          className="touch-friendly whitespace-nowrap"
        >
          Predictions
        </TabsTrigger>
        <TabsTrigger
          value="players"
          className="touch-friendly whitespace-nowrap"
        >
          Players
        </TabsTrigger>
        <TabsTrigger
          value="betting"
          className="touch-friendly whitespace-nowrap"
        >
          Betting
        </TabsTrigger>
        <TabsTrigger
          value="leaderboard"
          className="touch-friendly whitespace-nowrap"
        >
          Leaderboard
        </TabsTrigger>
        <TabsTrigger
          value="health"
          className="touch-friendly whitespace-nowrap"
        >
          Health
        </TabsTrigger>
      </TabsList>
    </div>
  );
}
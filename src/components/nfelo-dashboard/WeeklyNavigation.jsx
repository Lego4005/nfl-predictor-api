import React from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const WeeklyNavigation = ({ currentWeek, onWeekChange }) => {
  const handlePrevWeek = () => {
    if (currentWeek > 1) {
      onWeekChange(currentWeek - 1);
    }
  };

  const handleNextWeek = () => {
    if (currentWeek < 18) {
      onWeekChange(currentWeek + 1);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrevWeek}
        disabled={currentWeek === 1}
        className="p-2"
      >
        <ChevronLeft className="w-4 h-4" />
      </Button>
      
      <div className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg font-medium">
        Week {currentWeek}
      </div>
      
      <Button
        variant="outline"
        size="sm"
        onClick={handleNextWeek}
        disabled={currentWeek === 18}
        className="p-2"
      >
        <ChevronRight className="w-4 h-4" />
      </Button>
    </div>
  );
};

export default WeeklyNavigation;
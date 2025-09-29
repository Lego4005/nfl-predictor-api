import React, { useState, useMemo, useEffect } from "react";
import { GameCard } from "./GameCard";
import { Calendar, ChevronLeft, ChevronRight, Search, Filter } from "@/lib/icons";
import {
    startOfDay,
    addDays,
    toLocalYMD,
    fmtDateLong,
    fmtDateShort,
    groupBy,
    isNFLDay,
    clamp,
    classNames,
    TZ
} from "@/lib/nfl-utils";
import { GAMES, type Game } from "@/lib/nfl-data";

interface GamesBoardProps {
    onOpenGame: (game: Game) => void;
}

export const GamesBoard: React.FC<GamesBoardProps> = ({ onOpenGame }) => {
    const [query, setQuery] = useState('');
    const [selectedWeek, setSelectedWeek] = useState(3);
    const [status, setStatus] = useState<'ALL' | Game['status']>('ALL');
    const [reducedMotion, setReducedMotion] = useState(false);
    const [density, setDensity] = useState<'compact' | 'cozy' | 'comfy'>('compact');

    useEffect(() => {
        try {
            setReducedMotion(window?.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false);
        } catch { }
    }, []);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();

        return GAMES.filter((g) => {
            if (g.week !== selectedWeek) return false;
            if (status !== 'ALL' && g.status !== status) return false;
            if (!q) return true;

            // Search logic
            const searchTerms = [
                g.home, g.away,
            ];

            return searchTerms.some(term => term?.toLowerCase().includes(q));
        });
    }, [query, selectedWeek, status]);

    // Group games by day of week within the selected NFL week
    const groupedByDay = useMemo(() => {
        const gb = groupBy(filtered, (g) => {
            const gameDate = new Date(g.date);
            const dayOfWeek = gameDate.getDay();
            // Map day numbers to NFL day names
            const dayNames: Record<number, string> = {
                0: 'Sunday',
                1: 'Monday',
                4: 'Thursday',
                5: 'Friday',
                6: 'Saturday'
            };
            return dayNames[dayOfWeek] || 'Other';
        });

        for (const k in gb) {
            gb[k].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        }

        // Split Sunday games into multiple columns if more than 8 games
        if (gb['Sunday'] && gb['Sunday'].length > 8) {
            const sundayGames = gb['Sunday'];
            delete gb['Sunday'];

            for (let i = 0; i < sundayGames.length; i += 8) {
                const columnIndex = Math.floor(i / 8) + 1;
                const columnKey = columnIndex === 1 ? 'Sunday' : `Sunday ${columnIndex}`;
                gb[columnKey] = sundayGames.slice(i, i + 8);
            }
        }

        return gb;
    }, [filtered]);

    // Define the order of NFL days (Thu -> Sun -> Mon, with Sat for late season)
    const nflDayOrder = useMemo(() => {
        const baseDays = ['Thursday'];

        // Add multiple Sunday columns if needed
        const sundayColumns = [];
        if (groupedByDay['Sunday']) sundayColumns.push('Sunday');
        if (groupedByDay['Sunday 2']) sundayColumns.push('Sunday 2');
        if (groupedByDay['Sunday 3']) sundayColumns.push('Sunday 3');

        baseDays.push(...sundayColumns);
        baseDays.push('Monday');

        // Add Saturday for late season (week 15+)
        if (selectedWeek >= 15) {
            return ['Thursday', 'Saturday', ...sundayColumns, 'Monday'];
        }
        return baseDays;
    }, [selectedWeek, groupedByDay]);

    // Only show days that have games
    const daysWithGames = useMemo(() => {
        return nflDayOrder.filter(day => (groupedByDay[day] || []).length > 0);
    }, [nflDayOrder, groupedByDay]);

    const changeWeek = (direction: number) => {
        setSelectedWeek(current => clamp(current + direction, 1, 18));
    };

    const colsClass = density === 'compact'
        ? 'auto-cols-[280px]'  // Fixed width columns for compact
        : density === 'cozy'
            ? 'auto-cols-[minmax(320px,1fr)]'  // Medium columns
            : 'auto-cols-[minmax(380px,1fr)]'; // Large columns

    return (
        <div className="w-full">
            {/* Controls */}
            <section className="flex flex-wrap gap-3 items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => changeWeek(-1)}
                        className="p-2.5 rounded-xl border border-white/10 hover:bg-white/5 transition-colors"
                    >
                        <span className="text-lg">{ChevronLeft()}</span>
                    </button>
                    <div className="px-3 py-2 rounded-xl border border-white/10 glass flex items-center gap-2 text-sm">
                        <span className="text-lg">{Calendar()}</span>
                        <span className="font-medium">Week {selectedWeek}</span>
                    </div>
                    <button
                        onClick={() => changeWeek(1)}
                        className="p-2.5 rounded-xl border border-white/10 hover:bg-white/5 transition-colors"
                    >
                        <span className="text-lg">{ChevronRight()}</span>
                    </button>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">{Search()}</span>
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search team (e.g., KC, Eagles)"
                            className="pl-9 pr-3 py-2 rounded-xl glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary min-w-[240px]"
                        />
                    </div>

                    <div className="flex items-center gap-2 px-2.5 py-2 rounded-xl border border-white/10 glass">
                        <span className="text-muted-foreground">{Filter()}</span>
                        <select
                            className="bg-transparent text-sm focus:outline-none"
                            value={status}
                            onChange={(e) => setStatus(e.target.value as typeof status)}
                        >
                            <option value="ALL">All</option>
                            <option value="SCHEDULED">Scheduled</option>
                            <option value="LIVE">Live</option>
                            <option value="FINAL">Final</option>
                        </select>
                    </div>

                    <select
                        className="px-2.5 py-2 rounded-xl glass border border-white/10 text-sm focus:outline-none"
                        value={selectedWeek}
                        onChange={(e) => setSelectedWeek(Number(e.target.value))}
                    >
                        {Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
                            <option key={w} value={w}>Week {w}</option>
                        ))}
                    </select>

                    <div className="flex items-center gap-2 px-2.5 py-2 rounded-xl border border-white/10 glass">
                        <span className="text-sm opacity-80">View</span>
                        <select
                            className="bg-transparent text-sm focus:outline-none"
                            value={density}
                            onChange={(e) => setDensity(e.target.value as typeof density)}
                        >
                            <option value="compact">Compact</option>
                            <option value="cozy">Cozy</option>
                            <option value="comfy">Comfortable</option>
                        </select>
                    </div>
                </div>
            </section>

            {/* Grid */}
            <section className="mt-4">
                <div className={classNames('grid grid-flow-col', colsClass, density === 'compact' ? 'gap-3' : 'gap-5')}>
                    {daysWithGames.map((dayName, colIndex) => {
                        const games = groupedByDay[dayName] || [];

                        return (
                            <div key={dayName} className="flex flex-col min-h-[200px]">
                                <div className="mb-3 px-2 py-1.5 rounded-lg text-sm tracking-wide flex items-center gap-2 border bg-primary/15 text-primary-foreground border-primary/30">
                                    <span
                                        className="inline-block w-1.5 h-1.5 rounded-full"
                                        style={{ background: 'hsl(var(--primary))' }}
                                    />
                                    {dayName.startsWith('Sunday') && dayName !== 'Sunday' ? dayName : dayName}
                                    {dayName === 'Thursday' && ' Night'}
                                    {dayName === 'Monday' && ' Night'}
                                    {dayName === 'Saturday' && ' Games'}
                                    {(dayName === 'Sunday' || dayName.startsWith('Sunday')) && ' Games'}
                                </div>

                                {games.length === 0 ? (
                                    <div className="flex-1 grid place-items-center rounded-2xl border border-dashed border-white/15 glass text-sm text-muted-foreground p-6">
                                        No games
                                    </div>
                                ) : (
                                    <div className={classNames('flex flex-col', density === 'compact' ? 'gap-2' : 'gap-3')}>
                                        {games.map((g, rowIndex) => (
                                            <GameCard
                                                key={g.id}
                                                game={g}
                                                delayMs={(colIndex * 6 + rowIndex) * 35}
                                                reducedMotion={reducedMotion}
                                                compact={density === 'compact'}
                                                onOpen={onOpenGame}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </section>
        </div>
    );
};
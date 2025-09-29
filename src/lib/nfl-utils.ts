// NFL utility functions for date handling, Elo calculations, and NFL-specific logic

const TZ =
  Intl.DateTimeFormat().resolvedOptions().timeZone || "America/New_York";

export const clamp = (v: number, a: number, b: number): number =>
  Math.min(Math.max(v, a), b);

export const classNames = (
  ...classes: (string | undefined | null | false)[]
): string => classes.filter(Boolean).join(" ");

// Date utilities
export const startOfDay = (dateLike: Date | string): Date => {
  const d = new Date(dateLike);
  d.setHours(0, 0, 0, 0);
  return d;
};

export const addDays = (dateLike: Date | string, n: number): Date => {
  const d = new Date(dateLike);
  d.setDate(d.getDate() + n);
  return d;
};

export const toLocalYMD = (dateLike: Date | string): string => {
  const d = new Date(dateLike);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const da = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${da}`;
};

// Elo calculation (home advantage default ~55 Elo)
export const eloWinProb = (
  homeElo: number,
  awayElo: number,
  hca: number = 55
): number => 1 / (1 + Math.pow(10, -((homeElo + hca - awayElo) / 400)));

export const probToSpread = (pHome: number): number => 14 * (pHome - 0.5);

// Date formatting
export const fmtTime = (dateISO: string): string => {
  try {
    const d = new Date(dateISO);
    return new Intl.DateTimeFormat(undefined, {
      hour: "numeric",
      minute: "2-digit",
      timeZone: TZ,
    }).format(d);
  } catch {
    return "—";
  }
};

export const fmtDateLong = (dateISO: string): string => {
  try {
    const d = new Date(dateISO);
    return new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      timeZone: TZ,
    }).format(d);
  } catch {
    return "—";
  }
};

export const fmtDateShort = (dateISO: string): string => {
  try {
    const d = new Date(dateISO);
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      timeZone: TZ,
    }).format(d);
  } catch {
    return "—";
  }
};

// Array utility
export const groupBy = <T>(
  arr: T[],
  keyFn: (item: T) => string
): Record<string, T[]> =>
  arr.reduce(
    (acc, x) => {
      const k = keyFn(x);
      (acc[k] ||= []).push(x);
      return acc;
    },
    {} as Record<string, T[]>
  );

// NFL-specific date logic

// Thanksgiving: 4th Thursday of November
function thanksgivingOfYear(year: number): Date {
  const d = new Date(year, 10, 1); // Nov 1
  let thursdays = 0;
  while (d.getMonth() === 10) {
    if (d.getDay() === 4) {
      // Thursday
      thursdays += 1;
      if (thursdays === 4) return new Date(d);
    }
    d.setDate(d.getDate() + 1);
  }
  return new Date(year, 10, 28); // fallback
}

function isBlackFriday(dateLike: Date | string): boolean {
  const d = startOfDay(dateLike);
  const ty = d.getFullYear();
  const tg = thanksgivingOfYear(ty);
  const bf = addDays(tg, 1);
  return d.toDateString() === bf.toDateString();
}

// Base NFL days: Thu (4), Sun (0), Mon (1). Add Sat (6) in late season.
export function isNFLDay(
  dateLike: Date | string,
  weekNumber: number = 1
): boolean {
  const d = new Date(dateLike);
  const dow = d.getDay();
  if (dow === 0 || dow === 1 || dow === 4) return true; // Sun, Mon, Thu
  if (weekNumber >= 15 && dow === 6) return true; // Add Saturday in late season
  if (isBlackFriday(d)) return true; // Special Black Friday games
  return false;
}

export { TZ };

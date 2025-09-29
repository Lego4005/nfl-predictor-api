import React from "react";

interface IconProps extends React.SVGAttributes<SVGElement> {
    className?: string;
}

const IconBase = ({ className, children, ...props }: IconProps & { children: React.ReactNode }) => (
    <svg
        className={className}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
        {...props}
    >
        {children}
    </svg>
);

export const Calendar = (props: IconProps) => (
    <IconBase {...props}>
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
    </IconBase>
);

export const ChevronLeft = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="15 18 9 12 15 6" />
    </IconBase>
);

export const ChevronRight = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="9 18 15 12 9 6" />
    </IconBase>
);

export const Clock = (props: IconProps) => (
    <IconBase {...props}>
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </IconBase>
);

export const Search = (props: IconProps) => (
    <IconBase {...props}>
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </IconBase>
);

export const Star = (props: IconProps) => (
    <IconBase {...props}>
        <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9" />
    </IconBase>
);

export const Trophy = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M8 21h8" />
        <path d="M12 17v4" />
        <path d="M8 4h8v3a4 4 0 0 1-8 0z" />
        <path d="M4 7a4 4 0 0 0 4 4" />
        <path d="M20 7a4 4 0 0 1-4 4" />
    </IconBase>
);

export const TrendingUp = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
    </IconBase>
);

export const Globe2 = (props: IconProps) => (
    <IconBase {...props}>
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20" />
        <path d="M12 2a15.3 15.3 0 0 1 0 20a15.3 15.3 0 0 1 0-20" />
    </IconBase>
);

export const Filter = (props: IconProps) => (
    <IconBase {...props}>
        <polygon points="22 3 2 3 10 12 10 19 14 21 14 12 22 3" />
    </IconBase>
);

export const Football = (props: IconProps) => (
    <IconBase {...props}>
        <ellipse cx="12" cy="12" rx="10" ry="6" />
        <line x1="8" y1="12" x2="16" y2="12" />
        <line x1="10" y1="10" x2="14" y2="14" />
        <line x1="14" y1="10" x2="10" y2="14" />
    </IconBase>
);

export const HomeIcon = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M3 11l9-7 9 7" />
        <path d="M9 22V12h6v10" />
    </IconBase>
);

export const BarChart = (props: IconProps) => (
    <IconBase {...props}>
        <rect x="3" y="10" width="4" height="11" />
        <rect x="10" y="3" width="4" height="18" />
        <rect x="17" y="6" width="4" height="15" />
    </IconBase>
);

export const ChevronUp = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="18 15 12 9 6 15" />
    </IconBase>
);

export const ChevronDown = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="6 9 12 15 18 9" />
    </IconBase>
);

export const ArrowLeft = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M19 12H5" />
        <path d="M12 19l-7-7 7-7" />
    </IconBase>
);

export const TrendingDown = (props: IconProps) => (
    <IconBase {...props}>
        <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
        <polyline points="17 18 23 18 23 12" />
    </IconBase>
);

export const User = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
    </IconBase>
);

export const Brain = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
        <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
        <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
        <path d="M17.599 6.5a3 3 0 0 0 .399-1.375" />
        <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5" />
        <path d="M3.477 10.896a4 4 0 0 1 .585-.396" />
        <path d="M19.938 10.5a4 4 0 0 1 .585.396" />
        <path d="M6 18a4 4 0 0 1-1.967-.516" />
        <path d="M19.967 17.484A4 4 0 0 1 18 18" />
    </IconBase>
);

export const Sparkles = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
        <path d="M20 3v4" />
        <path d="M22 5h-4" />
        <path d="M4 17v2" />
        <path d="M5 18H3" />
    </IconBase>
);

export const MessageSquare = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </IconBase>
);

export const Zap = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M4 14a1 1 0 0 1-.78-1.63L9.9 4.2a2 2 0 0 1 3.76 1.06L12.8 9h3.7a1 1 0 0 1 .78 1.63l-6.68 8.17a2 2 0 0 1-3.76-1.06L7.2 14Z" />
    </IconBase>
);

export const MapPin = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
    </IconBase>
);

export const Target = (props: IconProps) => (
    <IconBase {...props}>
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
    </IconBase>
);

export const DollarSign = (props: IconProps) => (
    <IconBase {...props}>
        <line x1="12" y1="2" x2="12" y2="22" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </IconBase>
);

export const AlertTriangle = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
    </IconBase>
);

export const Award = (props: IconProps) => (
    <IconBase {...props}>
        <circle cx="12" cy="8" r="6" />
        <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11" />
    </IconBase>
);

export const Users = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </IconBase>
);

export const Calculator = (props: IconProps) => (
    <IconBase {...props}>
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <line x1="8" y1="6" x2="16" y2="6" />
        <line x1="16" y1="14" x2="16" y2="18" />
        <line x1="8" y1="14" x2="8" y2="18" />
        <line x1="12" y1="14" x2="12" y2="18" />
        <line x1="8" y1="10" x2="8" y2="10" />
        <line x1="12" y1="10" x2="12" y2="10" />
        <line x1="16" y1="10" x2="16" y2="10" />
    </IconBase>
);

export const Activity = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </IconBase>
);

export const Eye = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
        <circle cx="12" cy="12" r="3" />
    </IconBase>
);

export const Shield = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </IconBase>
);

export const Crown = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M2 18h20" />
        <path d="m7 14 5-5 5 5" />
        <path d="M2 18l2-6 4 2 4-6 4 6 4-2 2 6" />
    </IconBase>
);

export const Flame = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
    </IconBase>
);

export const Bot = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
    </IconBase>
);

export const Lightbulb = (props: IconProps) => (
    <IconBase {...props}>
        <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
        <path d="M9 18h6" />
        <path d="M10 22h4" />
    </IconBase>
);

// Aliases for consistency
export const BarChart3 = BarChart;
export const FlameIcon = Flame;
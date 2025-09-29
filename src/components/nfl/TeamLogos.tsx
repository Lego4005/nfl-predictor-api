import React from 'react';

interface TeamLogoProps {
    team: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    className?: string;
}

const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
};

// NFL Team SVG Logo Components
const TeamLogos: { [key: string]: React.FC<{ className?: string }> } = {
    KC: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#E31837" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">KC</text>
        </svg>
    ),

    BUF: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#00338D" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">BUF</text>
        </svg>
    ),

    PHI: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#004C54" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">PHI</text>
        </svg>
    ),

    DAL: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#041E42" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">DAL</text>
        </svg>
    ),

    SF: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#AA0000" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">SF</text>
        </svg>
    ),

    DET: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0076B6" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">DET</text>
        </svg>
    ),

    NYJ: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#125740" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">NYJ</text>
        </svg>
    ),

    NE: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#002244" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">NE</text>
        </svg>
    ),

    CIN: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#FB4F14" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">CIN</text>
        </svg>
    ),

    BAL: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#241773" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">BAL</text>
        </svg>
    ),

    MIA: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#008E97" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">MIA</text>
        </svg>
    ),

    LAR: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#003594" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">LAR</text>
        </svg>
    ),

    GB: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#203731" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">GB</text>
        </svg>
    ),

    MIN: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#4F2683" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">MIN</text>
        </svg>
    ),

    TB: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#D50A0A" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">TB</text>
        </svg>
    ),

    CAR: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0085CA" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">CAR</text>
        </svg>
    ),

    ATL: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#A71930" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">ATL</text>
        </svg>
    ),

    NO: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#D3BC8D" />
            <text x="50" y="60" textAnchor="middle" fill="#000" fontSize="24" fontWeight="bold">NO</text>
        </svg>
    ),

    SEA: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#002244" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">SEA</text>
        </svg>
    ),

    ARI: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#97233F" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">ARI</text>
        </svg>
    ),

    DEN: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#FB4F14" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">DEN</text>
        </svg>
    ),

    LV: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#000000" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">LV</text>
        </svg>
    ),

    LAC: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0080C6" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">LAC</text>
        </svg>
    ),

    HOU: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#03202F" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">HOU</text>
        </svg>
    ),

    IND: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#002C5F" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">IND</text>
        </svg>
    ),

    JAX: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#006778" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">JAX</text>
        </svg>
    ),

    TEN: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0C2340" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">TEN</text>
        </svg>
    ),

    CLE: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#311D00" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">CLE</text>
        </svg>
    ),

    PIT: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#FFB612" />
            <text x="50" y="60" textAnchor="middle" fill="#000" fontSize="20" fontWeight="bold">PIT</text>
        </svg>
    ),

    CHI: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0B162A" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">CHI</text>
        </svg>
    ),

    WAS: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#5A1414" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">WAS</text>
        </svg>
    ),

    NYG: ({ className }) => (
        <svg viewBox="0 0 100 100" className={className}>
            <circle cx="50" cy="50" r="45" fill="#0B2265" />
            <text x="50" y="60" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">NYG</text>
        </svg>
    ),
};

const TeamLogo: React.FC<TeamLogoProps> = ({ team, size = 'md', className = '' }) => {
    const LogoComponent = TeamLogos[team.toUpperCase()];

    if (!LogoComponent) {
        // Fallback for unknown teams
        return (
            <div className={`${sizeClasses[size]} ${className} rounded-full bg-gray-500 flex items-center justify-center`}>
                <span className="text-white font-bold text-xs">{team}</span>
            </div>
        );
    }

    return <LogoComponent className={`${sizeClasses[size]} ${className}`} />;
};

export default TeamLogo;
export { TeamLogos };
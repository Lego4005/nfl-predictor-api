import React from "react";

interface TeamLogoProps {
  teamAbbr: string;
  size?: "small" | "medium" | "large" | "xlarge";
  className?: string;
  style?: React.CSSProperties;
  showGlow?: boolean;
  animated?: boolean;
  alt?: string;
  onError?: () => void;
  [key: string]: any; // for additional props
}

declare const TeamLogo: React.FC<TeamLogoProps>;
export default TeamLogo;

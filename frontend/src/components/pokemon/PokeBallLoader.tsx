import React from "react";

interface PokeBallLoaderProps {
  size?: number;
  className?: string;
}

export function PokeBallLoader({ size = 32, className = "" }: PokeBallLoaderProps) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        className="animate-spin-pokeball"
      >
        {/* Outer boundary/outline */}
        <circle
          cx="16"
          cy="16"
          r="14"
          fill="none"
          stroke="var(--border-default)"
          strokeWidth="2"
        />
        {/* Top Red half */}
        <path
          d="M 3.05 16 A 13 13 0 0 1 28.95 16 Z"
          fill="var(--poke-red)"
        />
        {/* Bottom White half */}
        <path
          d="M 3.05 16 A 13 13 0 0 0 28.95 16 Z"
          fill="var(--text-primary)"
        />
        {/* Center divider line */}
        <line
          x1="2"
          y1="16"
          x2="30"
          y2="16"
          stroke="var(--border-default)"
          strokeWidth="2"
        />
        {/* Center circle button ring */}
        <circle
          cx="16"
          cy="16"
          r="4.5"
          fill="var(--bg-raised)"
          stroke="var(--border-default)"
          strokeWidth="2"
        />
        {/* Center button core */}
        <circle
          cx="16"
          cy="16"
          r="2"
          fill="var(--text-primary)"
        />
      </svg>
    </div>
  );
}

export default PokeBallLoader;

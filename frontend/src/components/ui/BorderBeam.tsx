import React from "react";

interface BorderBeamProps {
  duration?: number;
  borderWidth?: number;
  colorFrom?: string;
  colorTo?: string;
  className?: string;
  borderRadius?: string;
}

export function BorderBeam({
  duration = 4,
  borderWidth = 1.5,
  colorFrom = "#cfa240",
  colorTo = "#f1cd7c",
  className = "",
  borderRadius = "inherit",
}: BorderBeamProps) {
  return (
    <div
      className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`}
      style={{
        borderRadius,
        padding: `${borderWidth}px`,
        mask: "linear-gradient(#fff 0 0) content-box exclude, linear-gradient(#fff 0 0)",
        WebkitMask: "linear-gradient(#fff 0 0) content-box exclude, linear-gradient(#fff 0 0)",
        WebkitMaskComposite: "xor",
        maskComposite: "exclude",
      }}
    >
      <div
        className="absolute inset-[-200%] animate-[spin_5s_linear_infinite]"
        style={{
          background: `conic-gradient(from 0deg, transparent 70%, ${colorFrom} 85%, ${colorTo} 98%, transparent 100%)`,
          animationDuration: `${duration}s`,
        }}
      />
    </div>
  );
}

export default BorderBeam;

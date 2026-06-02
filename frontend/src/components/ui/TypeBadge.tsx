import { TYPE_COLORS } from "../../utils/pokemon";

interface TypeBadgeProps {
  type: string;
  size?: "sm" | "md";
}

export function TypeBadge({ type, size = "sm" }: TypeBadgeProps) {
  const normalizedType = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
  const color = TYPE_COLORS[normalizedType] ?? "#888888";
  
  // Format to hex with custom alpha
  const bgOpacity = "26"; // 15% in hex
  const borderOpacity = "66"; // 40% in hex
  
  const sizeClasses = size === "sm"
    ? "text-[10px] px-2 py-0.5 gap-1"
    : "text-xs px-2.5 py-1 gap-1.5";

  return (
    <span
      className={`inline-flex items-center font-bold uppercase tracking-wider select-none ${sizeClasses}`}
      style={{
        backgroundColor: `${color}${bgOpacity}`,
        borderColor: `${color}${borderOpacity}`,
        color: color,
        borderWidth: "1px",
        borderStyle: "solid",
        borderRadius: "var(--radius-sm)",
        fontFamily: "'Rajdhani', sans-serif"
      }}
    >
      <img
        src={`/pokemon-icons/types/${type.toLowerCase()}.svg`}
        alt=""
        className="w-3.5 h-3.5 object-contain"
        onError={(e) => {
          // If image fails to load, hide it
          (e.target as HTMLElement).style.display = "none";
        }}
      />
      <span>{type}</span>
    </span>
  );
}


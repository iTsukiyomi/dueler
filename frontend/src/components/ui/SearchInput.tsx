import { Search } from "lucide-react";

interface SearchInputProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  isLoading?: boolean;
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search...",
  autoFocus = false,
  isLoading = false,
}: SearchInputProps) {
  return (
    <div className="relative">
      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 flex items-center justify-center">
        <Search className="w-4 h-4 text-text-muted" />
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="w-full pl-10 pr-10 py-2.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-default)] text-text-primary placeholder:text-text-muted focus:border-[var(--poke-blue)] outline-none transition-all text-xs font-medium"
      />
      {isLoading && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-[var(--poke-blue)] border-t-transparent rounded-full animate-spin" />
      )}
    </div>
  );
}

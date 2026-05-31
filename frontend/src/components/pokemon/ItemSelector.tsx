import { useState } from "react";
import { useItemSearch } from "../../hooks/usePokemonData";
import { SearchInput } from "../ui/SearchInput";
import { displayName } from "../../utils/pokemon";

interface ItemSelectorProps {
  current: string;
  onChange: (item: string) => void;
}

export function ItemSelector({ current, onChange }: ItemSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const { data: results, isLoading } = useItemSearch(searchQuery);

  const handleSelectItem = (itemName: string) => {
    onChange(itemName);
    setSearchQuery("");
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange("");
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-bold uppercase tracking-wider text-text-muted">
        Held Item
      </label>
      <div className="relative">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="flex-1 flex items-center justify-between px-4 py-3.5 rounded-xl bg-bg-secondary/40 border border-border/60 hover:border-border text-left transition-all"
          >
            <span className="text-sm font-bold capitalize text-text-primary">
              {current ? displayName(current) : "No Item"}
            </span>
            <span className="text-text-muted">{isOpen ? "▲" : "▼"}</span>
          </button>
          {current && (
            <button
              type="button"
              onClick={handleClear}
              className="px-3 rounded-xl bg-bg-secondary/40 border border-border/60 hover:bg-rose-500/10 hover:border-rose-500/30 hover:text-rose-400 transition-all text-xs"
              title="Clear item"
            >
              Clear
            </button>
          )}
        </div>

        {isOpen && (
          <div className="absolute z-20 mt-2 w-full max-h-72 overflow-y-auto rounded-2xl bg-bg-card border border-border p-3 shadow-2xl backdrop-blur-xl animate-fadeIn">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search items (e.g. Choice Scarf)..."
              autoFocus
              isLoading={isLoading}
            />

            <div className="mt-3 space-y-1 max-h-48 overflow-y-auto pr-1">
              {results?.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleSelectItem(item.identifier)}
                  className="w-full flex items-center px-3 py-2.5 rounded-xl hover:bg-bg-secondary/80 text-sm font-medium transition-colors text-left"
                >
                  {item.display_name}
                </button>
              ))}

              {searchQuery.length > 0 && results?.length === 0 && !isLoading && (
                <div className="text-center py-6 text-text-muted text-xs">
                  No items found matching "{searchQuery}"
                </div>
              )}

              {searchQuery.length === 0 && (
                <div className="text-center py-6 text-text-muted text-xs">
                  Type to search items...
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

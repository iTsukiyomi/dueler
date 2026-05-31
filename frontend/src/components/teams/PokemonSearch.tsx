import { useState } from "react";
import { Modal } from "../ui/Modal";
import { SearchInput } from "../ui/SearchInput";
import { TypeBadge } from "../ui/TypeBadge";
import { usePokemonSearch } from "../../hooks/usePokemonData";
import type { GameDataPokemon } from "../../types";

interface PokemonSearchProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (pokemon: GameDataPokemon) => void;
}

export function PokemonSearch({ isOpen, onClose, onSelect }: PokemonSearchProps) {
  const [query, setQuery] = useState("");
  const { data: results, isLoading } = usePokemonSearch(query);

  const handleSelect = (poke: GameDataPokemon) => {
    onSelect(poke);
    setQuery("");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Choose a Pokémon" size="lg">
      <SearchInput
        value={query}
        onChange={setQuery}
        placeholder="Search Pokémon (e.g. Garchomp)..."
        autoFocus
        isLoading={isLoading}
      />

      <div className="mt-4 space-y-1 max-h-96 overflow-y-auto">
        {results?.map((poke) => (
          <button
            key={poke.identifier}
            onClick={() => handleSelect(poke)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-bg-card transition-colors text-left"
          >
            <img
              src={poke.sprite_url}
              alt={poke.display_name}
              className="w-10 h-10 object-contain"
              loading="lazy"
            />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">
                {poke.display_name}
              </div>
            </div>
            <div className="flex gap-1">
              {poke.types.map((t) => (
                <TypeBadge key={t} type={t} />
              ))}
            </div>
          </button>
        ))}

        {query.length > 0 && results?.length === 0 && !isLoading && (
          <div className="text-center py-8 text-text-muted text-sm">
            No Pokémon found matching "{query}"
          </div>
        )}

        {query.length === 0 && (
          <div className="text-center py-8 text-text-muted text-sm">
            Start typing to search
          </div>
        )}
      </div>
    </Modal>
  );
}

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTeamStore, PokemonSlot, createEmptyPokemon } from '@/stores/teamStore';
import { apiFetch } from '@/api/client';
import { 
  ArrowLeft, 
  Save, 
  Trash2, 
  Sparkles, 
  Search, 
  Dna, 
  BookOpen, 
  SlidersHorizontal,
  Plus,
  Compass
} from 'lucide-react';

interface GameDataPokemon {
  pokemon_id: number;
  identifier: string;
  display_name: string;
  sprite_url: string;
  types: string[];
}

interface GameDataAbility {
  ability_id: number;
  identifier: string;
  display_name: string;
  slot: number;
  is_hidden: boolean;
}

interface PokemonDetails {
  pokemon_id: number;
  identifier: string;
  display_name: string;
  sprite_url: string;
  sprite_url_shiny: string;
  types: string[];
  abilities: GameDataAbility[];
  learnset: string[];
}

interface GameDataMove {
  identifier: string;
  display_name: string;
  type_name: string;
  power: number | null;
  pp: number;
}

interface GameDataItem {
  identifier: string;
  display_name: string;
}

interface GameDataNature {
  identifier: string;
  display_name: string;
  increases_stat: string | null;
  decreases_stat: string | null;
}

export default function TeamEditorPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  
  const { currentTeam, fetchTeamDetails, updateTeam } = useTeamStore();

  // Local state for the team name and its pokemon slots
  const [teamName, setTeamName] = useState('');
  const [slots, setSlots] = useState<PokemonSlot[]>([]);
  const [activeSlotId, setActiveSlotId] = useState<number>(1);
  
  // Game data caching/catalogs
  const [natures, setNatures] = useState<GameDataNature[]>([]);
  const [pokemonSuggestions, setPokemonSuggestions] = useState<GameDataPokemon[]>([]);
  const [pokemonSearchQuery, setPokemonSearchQuery] = useState('');
  const [activePokemonDetails, setActivePokemonDetails] = useState<PokemonDetails | null>(null);
  
  // Auto-complete suggestions
  const [itemSuggestions, setItemSuggestions] = useState<GameDataItem[]>([]);
  const [itemSearchQuery, setItemSearchQuery] = useState('');
  const [showItemDropdown, setShowItemDropdown] = useState(false);
  
  const [moveSuggestions, setMoveSuggestions] = useState<GameDataMove[][]>([[], [], [], []]);
  const [moveSearchQueries, setMoveSearchQueries] = useState<string[]>(['', '', '', '']);
  const [showMoveDropdown, setShowMoveDropdown] = useState<boolean[]>([false, false, false, false]);

  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Load team details and base game data on mount
  useEffect(() => {
    if (!name) return;
    
    setLoading(true);
    
    // Fetch natures once
    apiFetch<GameDataNature[]>('/api/gamedata/natures')
      .then(setNatures)
      .catch(err => console.error('Failed to load natures', err));

    fetchTeamDetails(name)
      .then((team) => {
        if (team) {
          setTeamName(team.name);
          // Re-index slots immediately to guarantee unique 1-indexed IDs in frontend state
          const loadedSlots = (team.pokemon || []).map((s, idx) => ({
            ...s,
            id: idx + 1,
            // Ensure pokemon_id is present if resolved by backend
            pokemon_id: (s as any).pokemon_id || 0
          }));
          setSlots(loadedSlots);
          if (loadedSlots.length > 0) {
            setActiveSlotId(loadedSlots[0].id);
          }
        } else {
          setErrorMsg('Team not found');
        }
        setLoading(false);
      })
      .catch((err) => {
        setErrorMsg(err.message || 'Failed to load team');
        setLoading(false);
      });
  }, [name, fetchTeamDetails]);

  // Load active pokemon details (abilities, learnset, types) when the active slot changes
  const activeSlot = slots.find(s => s.id === activeSlotId);

  useEffect(() => {
    if (!activeSlot || !activeSlot.pokname) {
      setActivePokemonDetails(null);
      return;
    }

    apiFetch<PokemonDetails>(`/api/gamedata/pokemon/${activeSlot.pokname.toLowerCase()}`)
      .then((details) => {
        setActivePokemonDetails(details);
      })
      .catch(err => console.error('Failed to load Pokémon details', err));
      
    setItemSearchQuery(activeSlot.hitem || '');
    setMoveSearchQueries(activeSlot.moves.map(m => m || ''));
  }, [activeSlotId, activeSlot?.pokname]);

  // Search for pokemons based on query
  useEffect(() => {
    if (pokemonSearchQuery.trim().length === 0) {
      setPokemonSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(() => {
      apiFetch<GameDataPokemon[]>(`/api/gamedata/pokemon?q=${encodeURIComponent(pokemonSearchQuery)}&limit=10`)
        .then(setPokemonSuggestions)
        .catch(err => console.error(err));
    }, 200);

    return () => clearTimeout(delayDebounce);
  }, [pokemonSearchQuery]);

  // Search items
  useEffect(() => {
    if (itemSearchQuery.trim().length === 0) {
      setItemSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(() => {
      apiFetch<GameDataItem[]>(`/api/gamedata/items?q=${encodeURIComponent(itemSearchQuery)}&limit=10`)
        .then(setItemSuggestions)
        .catch(err => console.error(err));
    }, 200);

    return () => clearTimeout(delayDebounce);
  }, [itemSearchQuery]);

  // Search moves for each move slot
  const searchMovesForSlot = (query: string, slotIndex: number) => {
    const newQueries = [...moveSearchQueries];
    newQueries[slotIndex] = query;
    setMoveSearchQueries(newQueries);

    if (!activeSlot?.pokname) return;

    apiFetch<GameDataMove[]>(
      `/api/gamedata/moves?pokemon=${encodeURIComponent(activeSlot.pokname)}&q=${encodeURIComponent(query)}&limit=10`
    )
      .then((res) => {
        const newSuggestions = [...moveSuggestions];
        newSuggestions[slotIndex] = res;
        setMoveSuggestions(newSuggestions);
      })
      .catch(err => console.error(err));
  };

  // Update a single slot attribute
  const updateSlotField = (field: keyof PokemonSlot, value: any) => {
    setSlots(prev => prev.map(s => s.id === activeSlotId ? { ...s, [field]: value } : s));
  };

  // Select a pokemon for the active slot
  const selectPokemon = (p: GameDataPokemon) => {
    updateSlotField('pokname', p.identifier);
    updateSlotField('poknick', p.display_name);
    updateSlotField('pokemon_id', p.pokemon_id);
    updateSlotField('moves', ['', '', '', '']);
    updateSlotField('hitem', '');
    updateSlotField('ability_index', 0);
    setPokemonSearchQuery('');
    setPokemonSuggestions([]);
  };

  // Add new pokemon slot
  const addNewSlot = () => {
    if (slots.length >= 6) return;
    const nextId = Math.max(...slots.map(s => s.id), 0) + 1;
    const newSlot = createEmptyPokemon(nextId);
    setSlots([...slots, newSlot]);
    setActiveSlotId(nextId);
  };

  // Delete current slot
  const deleteActiveSlot = () => {
    if (slots.length <= 1) {
      // Clear instead of delete if only 1 slot
      setSlots([createEmptyPokemon(1)]);
      setActiveSlotId(1);
      return;
    }
    const remaining = slots.filter(s => s.id !== activeSlotId);
    // Re-index slots
    const reindexed = remaining.map((s, idx) => ({ ...s, id: idx + 1 }));
    setSlots(reindexed);
    setActiveSlotId(reindexed[0].id);
  };

  // Calculations for active pokemon EVs
  const evTotal = activeSlot 
    ? (activeSlot.hpev + activeSlot.atkev + activeSlot.defev + activeSlot.spatkev + activeSlot.spdefev + activeSlot.speedev)
    : 0;
  const evRemaining = 510 - evTotal;

  // Save team handler
  const handleSave = async () => {
    if (!name) return;
    setErrorMsg('');
    
    // Client-side validations
    for (let i = 0; i < slots.length; i++) {
      const s = slots[i];
      if (!s.pokname) {
        setErrorMsg(`Slot ${i + 1} does not have a Pokémon selected.`);
        return;
      }
      const evsSum = s.hpev + s.atkev + s.defev + s.spatkev + s.spdefev + s.speedev;
      if (evsSum > 510) {
        setErrorMsg(`Slot ${i + 1} (${s.poknick}) has ${evsSum} EVs, which exceeds the limit of 510.`);
        return;
      }
    }

    setSaving(true);
    try {
      await updateTeam(name, slots);
      alert('Squad saved successfully!');
      navigate('/dashboard/teams');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save squad');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-100">
        <div className="relative size-12">
          <div className="absolute inset-0 rounded-full border-4 border-orange-500/20 animate-pulse" />
          <div className="absolute inset-0 rounded-full border-4 border-t-orange-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full text-slate-100 min-h-screen pb-12">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Top bar with back and save buttons */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/20 p-5 rounded-2xl border border-slate-800/60 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Link 
              to="/dashboard/teams" 
              className="size-9 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center justify-center transition border border-slate-700"
            >
              <ArrowLeft className="size-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight capitalize text-white">
                Builder: {teamName}
              </h1>
              <p className="text-slate-400 text-xs mt-0.5">Customize stats, moves, items, and details for your battle roster.</p>
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm px-6 py-2.5 rounded-xl transition shadow-lg shadow-orange-600/15 disabled:opacity-50 shrink-0"
          >
            <Save className="size-4" />
            {saving ? 'Saving...' : 'Save Squad'}
          </button>
        </div>

        {errorMsg && (
          <div className="bg-red-500/15 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm font-semibold">
            {errorMsg}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Left panel: 6 Pokémon tabs */}
          <div className="lg:col-span-1 bg-slate-900/20 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md h-fit space-y-3">
            <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase px-1">Roster Slots</span>
            
            <div className="space-y-1.5">
              {slots.map((slot, index) => (
                <button
                  key={slot.id}
                  onClick={() => setActiveSlotId(slot.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl transition ${
                    activeSlotId === slot.id 
                      ? 'bg-gradient-to-r from-orange-600/20 to-red-500/10 border border-orange-500/50 text-orange-400 font-bold'
                      : 'bg-slate-950/20 border border-transparent text-slate-400 hover:bg-slate-950/50 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className="text-xs font-semibold font-mono text-slate-500">{index + 1}</span>
                    <span className="truncate capitalize text-sm">
                      {slot.pokname ? slot.pokname.replace(/-/g, ' ') : 'Empty Slot'}
                    </span>
                  </div>
                  {slot.pokname && (
                    <img 
                      src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${slot.shiny ? 'shiny/' : ''}${
                        (slot as any).pokemon_id || '0'
                      }.png`}
                      alt=""
                      className="size-7 object-contain drop-shadow"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  )}
                </button>
              ))}

              {slots.length < 6 && (
                <button
                  onClick={addNewSlot}
                  className="w-full flex items-center justify-center gap-2 p-3 border border-dashed border-slate-800 hover:border-slate-700 text-slate-500 hover:text-slate-400 rounded-xl transition text-xs font-bold"
                >
                  <Plus className="size-3.5" />
                  Add Pokemon
                </button>
              )}
            </div>
          </div>

          {/* Right panel: Active Pokémon Editor */}
          <div className="lg:col-span-3 bg-slate-900/20 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md space-y-6">
            
            {activeSlot ? (
              activeSlot.pokname ? (
                // Selected Pokémon Editor View
                <div className="space-y-6">
                  
                  {/* Title and stats bar */}
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-5">
                    <div className="flex items-center gap-4">
                      <div className="size-20 rounded-2xl bg-slate-950/60 border border-slate-850 flex items-center justify-center overflow-hidden shrink-0">
                        <img 
                          src={activeSlot.shiny && activePokemonDetails ? activePokemonDetails.sprite_url_shiny : activePokemonDetails?.sprite_url} 
                          alt={activeSlot.pokname} 
                          className="size-16 object-contain drop-shadow"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png';
                          }}
                        />
                      </div>
                      <div>
                        <div className="flex items-center gap-2.5">
                          <h2 className="text-xl font-bold capitalize text-slate-100">
                            {activeSlot.poknick || activeSlot.pokname.replace(/-/g, ' ')}
                          </h2>
                          {activePokemonDetails?.types.map((type) => (
                            <span 
                              key={type} 
                              className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border border-slate-800 bg-slate-950 text-slate-400"
                            >
                              {type}
                            </span>
                          ))}
                        </div>
                        <p className="text-xs text-slate-500 mt-1 capitalize">Original Species: {activeSlot.pokname.replace(/-/g, ' ')}</p>
                      </div>
                    </div>
                    <button
                      onClick={deleteActiveSlot}
                      className="flex items-center justify-center gap-2 bg-red-950/20 hover:bg-red-900/20 text-red-400 border border-red-900/25 px-4.5 py-2 rounded-xl transition text-xs font-bold w-full sm:w-auto"
                    >
                      <Trash2 className="size-3.5" />
                      Remove Slot
                    </button>
                  </div>

                  {/* Settings columns */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* Basic details form */}
                    <div className="space-y-4 bg-slate-950/30 border border-slate-900 p-5 rounded-2xl">
                      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-2">
                        <Dna className="size-4 text-orange-400" />
                        Trainer Specs
                      </h3>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Nickname</label>
                          <input 
                            type="text" 
                            value={activeSlot.poknick} 
                            onChange={(e) => updateSlotField('poknick', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Nature</label>
                          <select 
                            value={activeSlot.nature}
                            onChange={(e) => updateSlotField('nature', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100 capitalize"
                          >
                            {natures.map(n => (
                              <option key={n.identifier} value={n.display_name}>
                                {n.display_name} 
                                {n.increases_stat ? ` (+${n.increases_stat}/-${n.decreases_stat})` : ' (Neutral)'}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Level</label>
                          <input 
                            type="number" 
                            min={1} 
                            max={100}
                            value={activeSlot.pokelevel}
                            onChange={(e) => updateSlotField('pokelevel', parseInt(e.target.value) || 100)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Happiness</label>
                          <input 
                            type="number" 
                            min={0} 
                            max={255}
                            value={activeSlot.happiness}
                            onChange={(e) => updateSlotField('happiness', parseInt(e.target.value) || 255)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Gender</label>
                          <select 
                            value={activeSlot.gender}
                            onChange={(e) => updateSlotField('gender', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100"
                          >
                            <option value="M">Male (M)</option>
                            <option value="F">Female (F)</option>
                            <option value="N">Neutral (N)</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 pt-2">
                        {/* Ability selection */}
                        <div>
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Ability</label>
                          <select 
                            value={activeSlot.ability_index}
                            onChange={(e) => updateSlotField('ability_index', parseInt(e.target.value))}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-3 py-2 text-sm text-slate-100 capitalize"
                          >
                            {activePokemonDetails?.abilities.map((ab) => (
                              <option key={ab.ability_id} value={ab.slot - 1}>
                                {ab.display_name} {ab.is_hidden ? '(Hidden)' : ''}
                              </option>
                            ))}
                            {!activePokemonDetails?.abilities.length && (
                              <option value={0}>Default Ability</option>
                            )}
                          </select>
                        </div>

                        {/* Shiny toggle */}
                        <div className="flex items-center gap-2 mt-4 px-2">
                          <input 
                            type="checkbox" 
                            id="shiny-checkbox"
                            checked={activeSlot.shiny}
                            onChange={(e) => updateSlotField('shiny', e.target.checked)}
                            className="size-4 bg-slate-900 border border-slate-850 rounded focus:ring-orange-500/50 text-orange-600 focus:outline-none"
                          />
                          <label htmlFor="shiny-checkbox" className="text-xs font-bold text-slate-300 select-none cursor-pointer">
                            ✨ Shiny Form
                          </label>
                        </div>
                      </div>

                      {/* Held item autocomplete search */}
                      <div className="relative">
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Held Item</label>
                        <div className="relative">
                          <input 
                            type="text" 
                            placeholder="Search item..."
                            value={itemSearchQuery}
                            onChange={(e) => {
                              setItemSearchQuery(e.target.value);
                              updateSlotField('hitem', e.target.value);
                              setShowItemDropdown(true);
                            }}
                            onFocus={() => setShowItemDropdown(true)}
                            onBlur={() => setTimeout(() => setShowItemDropdown(false), 200)}
                            className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl pl-9 pr-4 py-2 text-sm text-slate-100"
                          />
                          <Search className="size-4 text-slate-500 absolute left-3 top-3" />
                        </div>

                        {showItemDropdown && itemSuggestions.length > 0 && (
                          <div className="absolute z-10 w-full bg-slate-950 border border-slate-800 rounded-xl mt-1.5 max-h-48 overflow-y-auto shadow-2xl p-1">
                            {itemSuggestions.map((item) => (
                              <button
                                key={item.identifier}
                                type="button"
                                onMouseDown={() => {
                                  updateSlotField('hitem', item.identifier);
                                  setItemSearchQuery(item.display_name);
                                  setShowItemDropdown(false);
                                }}
                                className="w-full text-left p-2 hover:bg-slate-900 rounded-lg text-sm text-slate-200 capitalize"
                              >
                                {item.display_name}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Moves set form */}
                    <div className="space-y-4 bg-slate-950/30 border border-slate-900 p-5 rounded-2xl">
                      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-2">
                        <BookOpen className="size-4 text-orange-400" />
                        Learnset Selection (4 moves)
                      </h3>

                      {activeSlot.moves.map((move, moveIdx) => (
                        <div key={moveIdx} className="relative">
                          <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
                            Move {moveIdx + 1}
                          </label>
                          
                          <div className="relative">
                            <input 
                              type="text" 
                              placeholder="Search move..."
                              value={moveSearchQueries[moveIdx]}
                              onChange={(e) => {
                                searchMovesForSlot(e.target.value, moveIdx);
                                const newMoves = [...activeSlot.moves];
                                newMoves[moveIdx] = e.target.value;
                                updateSlotField('moves', newMoves);
                                
                                const newShow = [...showMoveDropdown];
                                newShow[moveIdx] = true;
                                setShowMoveDropdown(newShow);
                              }}
                              onFocus={() => {
                                const newShow = [...showMoveDropdown];
                                newShow[moveIdx] = true;
                                setShowMoveDropdown(newShow);
                                searchMovesForSlot(moveSearchQueries[moveIdx], moveIdx);
                              }}
                              onBlur={() => setTimeout(() => {
                                const newShow = [...showMoveDropdown];
                                newShow[moveIdx] = false;
                                setShowMoveDropdown(newShow);
                              }, 200)}
                              className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl pl-9 pr-4 py-2 text-sm text-slate-100"
                            />
                            <Search className="size-4 text-slate-500 absolute left-3 top-3" />
                          </div>

                          {showMoveDropdown[moveIdx] && moveSuggestions[moveIdx]?.length > 0 && (
                            <div className="absolute z-10 w-full bg-slate-950 border border-slate-800 rounded-xl mt-1.5 max-h-48 overflow-y-auto shadow-2xl p-1">
                              {moveSuggestions[moveIdx].map((m) => (
                                <button
                                  key={m.identifier}
                                  type="button"
                                  onMouseDown={() => {
                                    const newMoves = [...activeSlot.moves];
                                    newMoves[moveIdx] = m.identifier;
                                    updateSlotField('moves', newMoves);

                                    const newQueries = [...moveSearchQueries];
                                    newQueries[moveIdx] = m.display_name;
                                    setMoveSearchQueries(newQueries);
                                    
                                    const newShow = [...showMoveDropdown];
                                    newShow[moveIdx] = false;
                                    setShowMoveDropdown(newShow);
                                  }}
                                  className="w-full text-left p-2 hover:bg-slate-900 rounded-lg text-sm text-slate-200 capitalize flex items-center justify-between"
                                >
                                  <span>{m.display_name}</span>
                                  <span className="text-[10px] font-bold text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded">
                                    {m.type_name}
                                  </span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                  </div>

                  {/* Stats Sliders (EVs & IVs) */}
                  <div className="bg-slate-950/30 border border-slate-900 p-5 rounded-2xl space-y-6">
                    <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                        <SlidersHorizontal className="size-4 text-orange-400" />
                        EV & IV Stat Customizer
                      </h3>
                      <div className="text-xs font-semibold">
                        Remaining EVs:{" "}
                        <span className={evRemaining < 0 ? 'text-red-500 font-extrabold' : 'text-orange-400 font-bold'}>
                          {evRemaining}
                        </span>
                        {" "}/ 510
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      
                      {/* Effort Values (EVs) */}
                      <div className="space-y-4">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Effort Values (EVs) - Max 252 per stat</span>
                        
                        {(['hpev', 'atkev', 'defev', 'spatkev', 'spdefev', 'speedev'] as const).map((stat) => {
                          const statLabels: Record<string, string> = {
                            hpev: 'HP', atkev: 'Attack', defev: 'Defense', spatkev: 'Sp. Atk', spdefev: 'Sp. Def', speedev: 'Speed'
                          };
                          const val = activeSlot[stat];

                          return (
                            <div key={stat} className="space-y-1.5">
                              <div className="flex justify-between text-xs font-medium text-slate-300">
                                <span>{statLabels[stat]}</span>
                                <span className="font-bold font-mono text-slate-200">{val}</span>
                              </div>
                              <input 
                                type="range"
                                min={0}
                                max={252}
                                value={val}
                                onChange={(e) => updateSlotField(stat, parseInt(e.target.value) || 0)}
                                className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-orange-500"
                              />
                            </div>
                          );
                        })}
                      </div>

                      {/* Individual Values (IVs) */}
                      <div className="space-y-4">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Individual Values (IVs) - Max 31 per stat</span>
                        
                        {(['hpiv', 'atkiv', 'defiv', 'spatkiv', 'spdefiv', 'speediv'] as const).map((stat) => {
                          const statLabels: Record<string, string> = {
                            hpiv: 'HP', atkiv: 'Attack', defiv: 'Defense', spatkiv: 'Sp. Atk', spdefiv: 'Sp. Def', speediv: 'Speed'
                          };
                          const val = activeSlot[stat];

                          return (
                            <div key={stat} className="space-y-1.5">
                              <div className="flex justify-between text-xs font-medium text-slate-300">
                                <span>{statLabels[stat]}</span>
                                <span className="font-bold font-mono text-slate-200">{val}</span>
                              </div>
                              <input 
                                type="range"
                                min={0}
                                max={31}
                                value={val}
                                onChange={(e) => updateSlotField(stat, parseInt(e.target.value) || 0)}
                                className="w-full h-1.5 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-slate-400"
                              />
                            </div>
                          );
                        })}
                      </div>

                    </div>
                  </div>

                </div>
              ) : (
                // Pokémon Selection Interface (when slot is empty)
                <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
                  <div className="size-16 rounded-full bg-slate-950 flex items-center justify-center border border-slate-800 shadow-inner">
                    <Compass className="size-7 text-orange-500 animate-pulse" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-200">No Pokémon in this slot</h3>
                    <p className="text-sm text-slate-500 max-w-sm mt-1">Search for a Pokémon species below to add it to your battle squad.</p>
                  </div>

                  <div className="relative w-full max-w-md">
                    <div className="relative">
                      <input 
                        type="text" 
                        placeholder="Type pokemon name (e.g. charizard)..."
                        value={pokemonSearchQuery}
                        onChange={(e) => setPokemonSearchQuery(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100"
                      />
                      <Search className="size-4 text-slate-500 absolute left-3.5 top-3.5" />
                    </div>

                    {pokemonSuggestions.length > 0 && (
                      <div className="absolute z-10 w-full bg-slate-950 border border-slate-800 rounded-xl mt-2 max-h-60 overflow-y-auto shadow-2xl p-1 text-left">
                        {pokemonSuggestions.map((p) => (
                          <button
                            key={p.pokemon_id}
                            type="button"
                            onClick={() => selectPokemon(p)}
                            className="w-full flex items-center gap-3 p-2 hover:bg-slate-900 rounded-lg text-sm text-slate-200 transition capitalize"
                          >
                            <img 
                              src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${p.pokemon_id}.png`}
                              alt="" 
                              className="size-8 object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png';
                              }}
                            />
                            <div className="flex flex-col">
                              <span className="font-semibold">{p.display_name}</span>
                              <span className="text-[10px] text-slate-500 font-medium tracking-wide">
                                {p.types.join(' / ')}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            ) : (
              <div className="text-center py-12 text-slate-500">Select or create a Pokémon slot to edit.</div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}

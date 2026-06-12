import React, { useEffect, useState } from 'react';
import { useTeamStore, TeamSummary, createEmptyPokemon } from '@/stores/teamStore';
import { useAuthStore } from '@/stores/authStore';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Empty, 
  EmptyHeader, 
  EmptyTitle, 
  EmptyDescription, 
  EmptyContent, 
  EmptyMedia 
} from '@/components/ui/empty';
import { 
  Swords, 
  Plus, 
  Upload, 
  Download, 
  Trash2, 
  Edit3, 
  CheckCircle2, 
  FileText, 
  X, 
  Clipboard,
  Sparkles
} from 'lucide-react';
import { parseShowdownTeam, exportShowdownTeam } from '@/utils/showdown';

export default function TeamListPage() {
  const { teams, fetchTeams, createTeam, deleteTeam, activateTeam, renameTeam, fetchTeamDetails } = useTeamStore();
  const { profile } = useAuthStore();
  const navigate = useNavigate();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [importName, setImportName] = useState('');
  const [importText, setImportText] = useState('');
  
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [exportText, setExportText] = useState('');
  
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState('');
  const [renameValue, setRenameValue] = useState('');

  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  // Create empty team and go to editor
  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    setErrorMsg('');
    try {
      // Create with one empty pokemon
      await createTeam(newTeamName, [createEmptyPokemon(1)]);
      setIsCreateOpen(false);
      navigate(`/dashboard/teams/${encodeURIComponent(newTeamName.trim().toLowerCase())}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create team');
    }
  };

  // Import Showdown team
  const handleImportShowdown = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importName.trim() || !importText.trim()) return;
    setErrorMsg('');
    try {
      const parsedSlots = parseShowdownTeam(importText);
      if (parsedSlots.length === 0) {
        setErrorMsg('Could not parse any Pokémon from the text. Check the format.');
        return;
      }
      await createTeam(importName, parsedSlots);
      setIsImportOpen(false);
      setImportText('');
      setImportName('');
      fetchTeams();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to import team');
    }
  };

  // Export Showdown team
  const handleExportShowdown = async (teamName: string) => {
    setErrorMsg('');
    try {
      const details = await fetchTeamDetails(teamName);
      if (details) {
        const text = exportShowdownTeam(details.pokemon);
        setExportText(text);
        setIsExportOpen(true);
      }
    } catch (err: any) {
      alert('Failed to export: ' + err.message);
    }
  };

  // Rename team
  const handleRenameTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameValue.trim() || !renameTarget) return;
    setErrorMsg('');
    try {
      await renameTeam(renameTarget, renameValue);
      setIsRenameOpen(false);
      fetchTeams();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to rename team');
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(exportText);
    alert('Copied to clipboard!');
  };

  return (
    <div className="w-full text-slate-100 min-h-screen pb-12">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/20 p-6 rounded-2xl border border-slate-800/60 backdrop-blur-md">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">My Battle Squads</h1>
            <p className="text-slate-400 text-sm mt-1">Create, edit, import/export, and activate your Pokémon battle teams.</p>
          </div>
          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            <button
              onClick={() => {
                setErrorMsg('');
                setNewTeamName('');
                setIsCreateOpen(true);
              }}
              className="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm px-4 py-2.5 rounded-xl transition shadow-lg shadow-orange-600/15 grow sm:grow-0"
            >
              <Plus className="size-4" />
              Create Squad
            </button>
            <button
              onClick={() => {
                setErrorMsg('');
                setImportName('');
                setImportText('');
                setIsImportOpen(true);
              }}
              className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-sm px-4 py-2.5 rounded-xl transition border border-slate-700 grow sm:grow-0"
            >
              <Upload className="size-4" />
              Import Showdown
            </button>
          </div>
        </div>

        {/* Team Grid */}
        {teams.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {teams.map((team) => (
              <div 
                key={team.name}
                className={`flex flex-col justify-between bg-slate-900/20 border rounded-2xl p-6 backdrop-blur-md transition duration-300 relative ${
                  team.is_active 
                    ? 'border-orange-500/80 shadow-lg shadow-orange-500/5' 
                    : 'border-slate-800/80 hover:border-slate-700/80'
                }`}
              >
                {/* Active Indicator */}
                {team.is_active && (
                  <div className="absolute top-4 right-4 flex items-center gap-1 bg-orange-500/15 border border-orange-500/30 text-orange-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                    <CheckCircle2 className="size-3" />
                    Active Squad
                  </div>
                )}

                {/* Team Info */}
                <div>
                  <h3 className="text-xl font-bold capitalize text-slate-200 pr-24 truncate">
                    {team.name}
                  </h3>
                  <span className="text-slate-500 text-xs mt-1 block">
                    Last updated: {new Date(team.updated_at).toLocaleDateString()}
                  </span>

                  {/* Pokémon Roster Sprites */}
                  <div className="flex items-center flex-wrap gap-2 mt-6 bg-slate-950/40 p-3 rounded-xl border border-slate-900/60 min-h-[72px]">
                    {team.pokemon && team.pokemon.length > 0 ? (
                      team.pokemon.map((p, idx) => (
                        <div key={idx} className="relative group/poke cursor-pointer" title={p.pokname}>
                          <img 
                            src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${p.shiny ? 'shiny/' : ''}${p.pokemon_id}.png`}
                            alt={p.pokname}
                            className="size-12 object-contain drop-shadow-[0_1px_4px_rgba(0,0,0,0.5)] group-hover/poke:scale-110 transition duration-200"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png';
                            }}
                          />
                        </div>
                      ))
                    ) : (
                      <span className="text-slate-600 text-xs">No Pokémon in squad. Click Edit to add some.</span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center justify-between gap-3 mt-6 pt-4 border-t border-slate-900/60">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleExportShowdown(team.name)}
                      className="size-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center justify-center transition"
                      title="Export Showdown"
                    >
                      <Download className="size-4" />
                    </button>
                    <button
                      onClick={() => {
                        setRenameTarget(team.name);
                        setRenameValue(team.name);
                        setIsRenameOpen(true);
                      }}
                      className="size-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center justify-center transition"
                      title="Rename Squad"
                    >
                      <Edit3 className="size-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Are you sure you want to delete "${team.name}"?`)) {
                          deleteTeam(team.name).then(() => fetchTeams());
                        }
                      }}
                      className="size-9 rounded-lg bg-red-950/20 hover:bg-red-900/20 text-red-400 border border-red-900/25 flex items-center justify-center transition"
                      title="Delete Squad"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>

                  <div className="flex gap-2">
                    <Link
                      to={`/dashboard/teams/${encodeURIComponent(team.name)}`}
                      className="bg-slate-800 hover:bg-slate-750 text-slate-200 font-semibold text-xs px-3.5 py-2 rounded-lg transition border border-slate-700"
                    >
                      Edit Squad
                    </Link>
                    {!team.is_active && (
                      <button
                        onClick={() => activateTeam(team.name).then(() => fetchTeams()).catch(err => alert(err.message))}
                        className="bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs px-3.5 py-2 rounded-lg transition"
                      >
                        Activate
                      </button>
                    )}
                  </div>
                </div>

              </div>
            ))}
          </div>
        ) : (
          <Empty className="bg-slate-900/20 border-slate-800/80 rounded-2xl py-16">
            <EmptyMedia variant="icon" className="bg-slate-850 text-orange-400 size-12 border border-slate-750">
              <Swords className="size-6" />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle className="text-slate-200 text-xl font-bold">No Battle Squads Found</EmptyTitle>
              <EmptyDescription className="text-slate-400 mt-2">
                Create a squad from scratch or import one in Pokémon Showdown format to start battling.
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent className="flex flex-col sm:flex-row gap-2 mt-4">
              <button
                onClick={() => {
                  setErrorMsg('');
                  setNewTeamName('');
                  setIsCreateOpen(true);
                }}
                className="bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm px-5 py-2 rounded-xl transition"
              >
                Create Squad
              </button>
              <button
                onClick={() => {
                  setErrorMsg('');
                  setImportName('');
                  setImportText('');
                  setIsImportOpen(true);
                }}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-sm px-5 py-2 rounded-xl transition"
              >
                Import Showdown
              </button>
            </EmptyContent>
          </Empty>
        )}

        {/* MODAL: CREATE TEAM */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-950 border border-slate-800 w-full max-w-md rounded-2xl p-6 relative">
              <button 
                onClick={() => setIsCreateOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="size-5" />
              </button>
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4">
                <Sparkles className="size-5 text-orange-400" />
                Create New Squad
              </h3>
              <form onSubmit={handleCreateTeam} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-400 mb-1.5">Squad Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Weather Team"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-4 py-2.5 text-sm text-slate-100"
                  />
                </div>
                {errorMsg && <p className="text-red-500 text-xs">{errorMsg}</p>}
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm py-2.5 rounded-xl transition"
                >
                  Create and Customize
                </button>
              </form>
            </div>
          </div>
        )}

        {/* MODAL: IMPORT SHOWDOWN */}
        {isImportOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-950 border border-slate-800 w-full max-w-xl rounded-2xl p-6 relative">
              <button 
                onClick={() => setIsImportOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="size-5" />
              </button>
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-2">
                <Upload className="size-5 text-orange-400" />
                Import Pokémon Showdown Team
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Paste your Pokémon Showdown format text block below. We will parse it and create your squad.
              </p>
              <form onSubmit={handleImportShowdown} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-400 mb-1.5">Squad Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Showdown Import"
                    value={importName}
                    onChange={(e) => setImportName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-4 py-2.5 text-sm text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-400 mb-1.5">Showdown Text</label>
                  <textarea
                    required
                    rows={8}
                    placeholder="Charizard @ Life Orb&#10;Ability: Blaze&#10;EVs: 252 Atk / 4 SpD / 252 Spe&#10;Jolly Nature&#10;- Flare Blitz&#10;- Dragon Claw&#10;- Earthquake&#10;- Roost"
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl p-4 text-sm text-slate-100 font-mono leading-relaxed"
                  />
                </div>
                {errorMsg && <p className="text-red-500 text-xs">{errorMsg}</p>}
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm py-2.5 rounded-xl transition"
                >
                  Import Squad
                </button>
              </form>
            </div>
          </div>
        )}

        {/* MODAL: EXPORT SHOWDOWN */}
        {isExportOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-950 border border-slate-800 w-full max-w-lg rounded-2xl p-6 relative">
              <button 
                onClick={() => setIsExportOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="size-5" />
              </button>
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-2">
                <FileText className="size-5 text-orange-400" />
                Export Showdown Format
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Copy the text block below to paste directly into Pokémon Showdown.
              </p>
              <div className="space-y-4">
                <textarea
                  readOnly
                  rows={10}
                  value={exportText}
                  className="w-full bg-slate-900 border border-slate-850 outline-none rounded-xl p-4 text-sm text-slate-100 font-mono leading-relaxed resize-none"
                />
                <button
                  onClick={copyToClipboard}
                  className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm py-2.5 rounded-xl transition"
                >
                  <Clipboard className="size-4" />
                  Copy to Clipboard
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: RENAME TEAM */}
        {isRenameOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-950 border border-slate-800 w-full max-w-md rounded-2xl p-6 relative">
              <button 
                onClick={() => setIsRenameOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="size-5" />
              </button>
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4">
                <Edit3 className="size-5 text-orange-400" />
                Rename Squad
              </h3>
              <form onSubmit={handleRenameTeam} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-400 mb-1.5">New Squad Name</label>
                  <input
                    type="text"
                    required
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-850 focus:border-orange-500/50 outline-none rounded-xl px-4 py-2.5 text-sm text-slate-100"
                  />
                </div>
                {errorMsg && <p className="text-red-500 text-xs">{errorMsg}</p>}
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm py-2.5 rounded-xl transition"
                >
                  Save Changes
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

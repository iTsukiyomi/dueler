import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTeamsList, useCreateTeam } from "../hooks/useTeams";
import { TeamCard } from "../components/teams/TeamCard";
import { defaultPokemonSlot } from "../types";

function TeamListSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between border-b border-border/30 pb-4">
        <div className="space-y-2">
          <div className="h-8 w-36 bg-bg-card/85 rounded-lg" />
          <div className="h-4 w-48 bg-bg-card/45 rounded-lg" />
        </div>
        <div className="h-10 w-28 bg-bg-card/60 rounded-xl" />
      </div>

      {/* Grid Cards Skeleton */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-bg-card/30 border border-border/40 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

export function TeamListPage() {
  const { data: teams, isLoading } = useTeamsList();
  const navigate = useNavigate();
  const createTeam = useCreateTeam();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");

  const handleCreate = () => {
    if (!newName.trim()) return;
    createTeam.mutate(
      { name: newName.trim(), pokemon: [defaultPokemonSlot()] },
      {
        onSuccess: (team) => {
          setShowCreate(false);
          setNewName("");
          navigate(`/dashboard/teams/${encodeURIComponent(team.name)}`);
        },
      },
    );
  };

  if (isLoading) {
    return <TeamListSkeleton />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 w-full select-none"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/30 pb-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-wider text-text-primary uppercase">
            Battle Squads
          </h1>
          <p className="text-xs text-text-muted mt-1 font-medium">Configure and select active six-Pokémon teams</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-5 py-3 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-widest hover:bg-accent-glow transition-all duration-300 cursor-pointer shadow-lg shadow-accent/10 shrink-0"
        >
          + New Squad
        </button>
      </div>

      {/* Create Team Inline Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-2xl bg-bg-card/25 border border-border/60 p-5 space-y-4">
              <div className="text-[10px] uppercase font-bold text-accent tracking-widest">Register New Battle Squad</div>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Enter unique squad name..."
                  maxLength={32}
                  autoFocus
                  className="flex-1 px-4 py-3 rounded-xl bg-bg-secondary/50 border border-border/60 text-text-primary placeholder:text-text-muted focus:border-accent outline-none text-xs font-bold uppercase tracking-wider"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleCreate}
                    disabled={createTeam.isPending || !newName.trim()}
                    className="px-5 py-3 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-wider hover:bg-accent-glow transition-all disabled:opacity-50 cursor-pointer shrink-0"
                  >
                    {createTeam.isPending ? "Syncing..." : "Create"}
                  </button>
                  <button
                    onClick={() => {
                      setShowCreate(false);
                      setNewName("");
                    }}
                    className="px-5 py-3 rounded-xl bg-bg-secondary/40 border border-border/60 text-text-muted hover:text-text-primary text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer shrink-0"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Teams Grid */}
      {teams && teams.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {teams.map((team, idx) => (
            <motion.div
              key={team.name}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.04 }}
            >
              <TeamCard
                name={team.name}
                pokemon={team.pokemon}
                isActive={team.is_active}
                onClick={() => navigate(`/dashboard/teams/${encodeURIComponent(team.name)}`)}
              />
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 rounded-2xl bg-bg-card/10 border border-dashed border-border/40">
          <div className="text-5xl mb-4 select-none">🎒</div>
          <div className="font-display text-lg font-bold text-text-secondary">No Battle Squads Configured</div>
          <div className="text-[10px] mt-1.5 text-text-muted font-bold uppercase tracking-widest max-w-xs mx-auto leading-relaxed">
            Register your first team assembly to deploy active fighters in battles
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-6 px-6 py-3 rounded-xl bg-accent/10 border border-accent/25 text-accent font-display font-bold text-xs uppercase tracking-widest hover:bg-accent hover:text-bg-primary transition-all duration-350 cursor-pointer"
          >
            Deploy First Squad
          </button>
        </div>
      )}
    </motion.div>
  );
}

export default TeamListPage;
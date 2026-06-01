import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTeamsList, useCreateTeam } from "../hooks/useTeams";
import { TeamCard } from "../components/teams/TeamCard";
import { defaultPokemonSlot } from "../types";

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
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 select-none w-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/40 pb-4">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">Teams</h1>
          <p className="text-xs text-text-muted mt-1">{teams?.length || 0} battle parties created</p>
        </div>
        <motion.button
          onClick={() => setShowCreate(true)}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          className="px-6 py-3 rounded-xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 cursor-pointer shadow-lg shadow-accent/20"
        >
          + New Team
        </motion.button>
      </div>

      {/* Create team form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-2xl bg-bg-card/50 border border-border p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Name your legendary squad..."
                  maxLength={32}
                  autoFocus
                  className="flex-1 px-5 py-3.5 rounded-xl bg-bg-secondary/60 border border-border/60 text-text-primary placeholder:text-text-muted focus:border-accent outline-none text-sm font-semibold"
                />
                <div className="flex gap-3">
                  <button
                    onClick={handleCreate}
                    disabled={createTeam.isPending || !newName.trim()}
                    className="px-6 py-3.5 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-wider hover:bg-accent-soft transition-all disabled:opacity-50 cursor-pointer"
                  >
                    {createTeam.isPending ? "Creating..." : "Create Team"}
                  </button>
                  <button
                    onClick={() => { setShowCreate(false); setNewName(""); }}
                    className="px-6 py-3.5 rounded-xl bg-bg-secondary/40 border border-border/60 text-text-muted hover:text-text-primary text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Teams grid */}
      {teams && teams.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {teams.map((team, idx) => (
            <motion.div
              key={team.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
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
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-20 rounded-2xl bg-bg-card/10 border border-dashed border-border/40"
        >
          <div className="text-6xl mb-4">🎒</div>
          <div className="font-display text-xl font-bold text-text-secondary tracking-wide">No Teams Yet</div>
          <div className="text-sm mt-2 text-text-muted max-w-sm mx-auto">
            Create your first battle party to start competing in the arena
          </div>
          <motion.button
            onClick={() => setShowCreate(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="mt-6 px-8 py-3 rounded-xl bg-accent/10 border border-accent/30 text-accent font-display font-bold text-xs uppercase tracking-widest hover:bg-accent hover:text-bg-primary transition-all"
          >
            Create First Team
          </motion.button>
        </motion.div>
      )}
    </motion.div>
  );
}

export default TeamListPage;
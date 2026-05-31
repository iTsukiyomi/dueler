import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTeamsList, useCreateTeam } from "../../hooks/useTeams";
import { TeamCard } from "./TeamCard";
import { defaultPokemonSlot } from "../../types";

export function TeamList() {
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
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Teams</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 rounded-xl bg-accent text-white font-medium text-sm hover:bg-accent-soft transition-colors"
        >
          + New Team
        </button>
      </div>

      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 rounded-2xl bg-bg-card border border-border p-4 overflow-hidden"
          >
            <div className="flex gap-3">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                placeholder="Team name..."
                maxLength={32}
                autoFocus
                className="flex-1 px-4 py-2 rounded-xl bg-bg-secondary border border-border text-text-primary placeholder:text-text-muted focus:border-accent outline-none text-sm"
              />
              <button
                onClick={handleCreate}
                disabled={createTeam.isPending || !newName.trim()}
                className="px-4 py-2 rounded-xl bg-accent text-white font-medium text-sm hover:bg-accent-soft transition-colors disabled:opacity-50"
              >
                {createTeam.isPending ? "Creating..." : "Create"}
              </button>
              <button
                onClick={() => { setShowCreate(false); setNewName(""); }}
                className="px-3 py-2 rounded-xl text-text-muted hover:text-text-primary text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {teams && teams.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {teams.map((team) => (
            <TeamCard
              key={team.name}
              name={team.name}
              pokemon={team.pokemon}
              isActive={team.is_active}
              onClick={() =>
                navigate(`/dashboard/teams/${encodeURIComponent(team.name)}`)
              }
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-text-muted">
          <div className="text-4xl mb-3">🎒</div>
          <div className="font-medium">No teams yet</div>
          <div className="text-sm mt-1">
            Create your first team to get started
          </div>
        </div>
      )}
    </motion.div>
  );
}

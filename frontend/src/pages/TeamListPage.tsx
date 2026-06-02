import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTeamsList, useCreateTeam } from "../hooks/useTeams";
import { TeamCard } from "../components/teams/TeamCard";
import { defaultPokemonSlot } from "../types";
import { Plus, FolderPlus, FolderOpen, X } from "lucide-react";

function TeamListSkeleton() {
  return (
    <div className="space-y-6 animate-pulse w-full">
      <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-4">
        <div className="space-y-2">
          <div className="h-3 w-28 bg-[var(--bg-raised)] rounded" />
          <div className="h-8 w-36 bg-[var(--bg-raised)] rounded" />
        </div>
        <div className="h-10 w-28 bg-[var(--bg-raised)] rounded" />
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded" />
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8 w-full select-none"
    >
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-4">
        <div>
          <div className="mono text-[10px] text-text-muted uppercase tracking-widest mb-1">
            Terminal / Battle Squads
          </div>
          <h1 className="font-display text-2xl font-bold text-text-primary uppercase tracking-tight">
            Squad Registry
          </h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Squad</span>
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
            <div className="card p-5 space-y-4 border-l-2 border-[var(--poke-yellow)]">
              <div className="font-rajdhani text-xs font-bold text-[var(--poke-yellow)] tracking-widest uppercase flex items-center gap-2">
                <FolderPlus className="w-4 h-4" />
                <span>Register New Battle Squad</span>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Enter unique squad name..."
                  maxLength={32}
                  autoFocus
                  className="input uppercase tracking-wider font-bold"
                />
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={handleCreate}
                    disabled={createTeam.isPending || !newName.trim()}
                    className="btn-primary"
                  >
                    <span>{createTeam.isPending ? "Syncing..." : "Establish"}</span>
                  </button>
                  <button
                    onClick={() => {
                      setShowCreate(false);
                      setNewName("");
                    }}
                    className="btn-secondary"
                  >
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
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
              initial={{ opacity: 0, y: 12 }}
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
        <div className="text-center py-16 rounded-[var(--radius-lg)] bg-[var(--bg-raised)] border border-dashed border-[var(--border-default)] flex flex-col items-center justify-center">
          <FolderOpen className="w-12 h-12 text-text-muted mb-4" />
          <h3 className="font-display text-base font-bold text-text-secondary uppercase tracking-wide">
            Registry Database Empty
          </h3>
          <div className="mono text-[9px] mt-1.5 text-text-muted tracking-widest max-w-xs mx-auto uppercase">
            Create your first squad matrix to deploy active fighters in battle servers.
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="btn-primary mt-6"
          >
            <Plus className="w-4 h-4" />
            <span>Deploy First Squad</span>
          </button>
        </div>
      )}
    </motion.div>
  );
}

export default TeamListPage;
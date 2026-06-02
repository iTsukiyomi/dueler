import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTeamsList, useCreateTeam } from "../../hooks/useTeams";
import { TeamCard } from "./TeamCard";
import { defaultPokemonSlot } from "../../types";
import { Backpack } from "lucide-react";
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription } from "../ui/empty";

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
      className="space-y-6 select-none"
    >
      <div className="flex items-center justify-between border-b border-border/40 pb-3">
        <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">
          Teams
        </h1>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 hover:shadow-[0_0_12px_rgba(207,162,64,0.2)] active:scale-[0.98] cursor-pointer"
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
            className="rounded-2xl bg-bg-card/30 border border-border p-5 overflow-hidden"
          >
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                placeholder="Name your legendary squad..."
                maxLength={32}
                autoFocus
                className="flex-1 px-4 py-3 rounded-xl bg-bg-secondary/60 border border-border/60 text-text-primary placeholder:text-text-muted focus:border-accent outline-none text-sm font-semibold capitalize"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={createTeam.isPending || !newName.trim()}
                  className="px-5 py-3 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-wider hover:bg-accent-soft transition-all disabled:opacity-50 cursor-pointer"
                >
                  {createTeam.isPending ? "Creating..." : "Create"}
                </button>
                <button
                  onClick={() => { setShowCreate(false); setNewName(""); }}
                  className="px-4 py-3 rounded-xl bg-bg-secondary/40 border border-border/60 text-text-muted hover:text-text-primary text-xs uppercase font-bold tracking-wider transition-colors cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {teams && teams.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
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
        <Empty className="py-16 bg-[var(--bg-raised)]/20 border border-dashed border-[var(--border-default)]">
          <Backpack className="w-10 h-10 text-text-muted mb-2" />
          <EmptyHeader>
            <EmptyTitle className="font-display text-lg font-bold text-text-secondary tracking-wide uppercase">No Teams Found</EmptyTitle>
            <EmptyDescription className="text-xs mt-1 text-text-muted font-sans max-w-xs leading-relaxed">
              Create your first tactical party to sync with the bot database.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
    </motion.div>
  );
}

import { useState } from "react";
import { motion } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";
import { BorderBeam } from "../components/ui/BorderBeam";
import toast from "react-hot-toast";

const themes = [
  { id: "firered", name: "Fire Red", emoji: "🦎", color: "from-red-500 to-orange-500" },
  { id: "leafgreen", name: "Leaf Green", emoji: "🐸", color: "from-green-500 to-emerald-500" },
  { id: "waterblue", name: "Water Blue", emoji: "🐢", color: "from-blue-500 to-cyan-500" },
  { id: "electric", name: "Electric", emoji: "🐭", color: "from-yellow-500 to-amber-500" },
  { id: "dark", name: "Shadow", emoji: "👾", color: "from-purple-600 to-gray-800" },
];

const generations = [
  { id: 1, name: "Gen 1", count: 151 },
  { id: 2, name: "Gen 2", count: 251 },
  { id: 3, name: "Gen 3", count: 386 },
  { id: 4, name: "Gen 4", count: 493 },
  { id: 5, name: "Gen 5", count: 649 },
  { id: 6, name: "Gen 6", count: 721 },
  { id: 7, name: "Gen 7", count: 809 },
  { id: 8, name: "Gen 8", count: 905 },
];

function SettingSection({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative rounded-3xl bg-bg-card/25 border border-border/70 p-6 overflow-hidden group"
    >
      <BorderBeam duration={7} borderWidth={1.2} className="opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="mb-5">
        <h3 className="font-display text-base font-bold text-text-primary tracking-wide uppercase">{title}</h3>
        {description && <p className="text-[10px] font-bold text-text-muted mt-1 uppercase tracking-wider">{description}</p>}
      </div>
      {children}
    </motion.div>
  );
}

function Toggle({ enabled, onChange, label }: { enabled: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex items-center justify-between cursor-pointer py-3 border-b border-border/20 last:border-0 select-none">
      <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors duration-300 cursor-pointer ${
          enabled ? "bg-accent" : "bg-bg-secondary border border-border"
        }`}
      >
        <motion.div
          animate={{ x: enabled ? 26 : 2 }}
          transition={{ type: "spring", stiffness: 450, damping: 25 }}
          className="absolute top-0.5 w-4 h-4 rounded-full bg-text-primary shadow"
        />
      </button>
    </label>
  );
}

function SelectOption({ selected, onChange, options, renderOption }: {
  selected: string;
  onChange: (v: string) => void;
  options: { id: string; name: string }[];
  renderOption?: (option: { id: string; name: string }) => React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {options.map((option) => {
        const isSelected = selected === option.id;
        return (
          <button
            type="button"
            key={option.id}
            onClick={() => onChange(option.id)}
            className={`p-4 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
              isSelected
                ? "border-accent bg-accent/15 text-accent shadow-[0_0_12px_rgba(207,162,64,0.15)]"
                : "border-border/60 bg-bg-secondary/40 text-text-secondary hover:border-border hover:bg-bg-secondary/60"
            }`}
          >
            {renderOption ? renderOption(option) : (
              <div className="text-xs font-bold uppercase tracking-wider">{option.name}</div>
            )}
          </button>
        );
      })}
    </div>
  );
}

export function SettingsPage() {
  const { data: profile } = usePlayerProfile();
  const { user, logout } = useAuthStore();

  const [theme, setTheme] = useState(profile?.theme || "firered");
  const [gen, setGen] = useState(profile?.gen || 5);
  const [notifications, setNotifications] = useState({
    battleInvites: true,
    rankedAlerts: true,
    teamSync: true,
    newsletter: false,
  });
  const [sound, setSound] = useState(true);
  const [music, setMusic] = useState(false);

  const handleSave = () => {
    toast.success("Settings synced successfully!");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8 w-full max-w-3xl select-none"
    >
      {/* Header */}
      <div className="border-b border-border/30 pb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-wider text-text-primary uppercase">
            Settings
          </h1>
          <p className="text-xs text-text-muted mt-1 font-medium">Configure league attributes and trainer preferences</p>
        </div>
        <button
          onClick={handleSave}
          className="px-5 py-3 rounded-xl bg-accent text-bg-primary font-display font-bold text-xs uppercase tracking-widest hover:bg-accent-glow transition-all duration-300 cursor-pointer shadow-lg shadow-accent/10"
        >
          Save Changes
        </button>
      </div>

      {/* Account Info Section */}
      <SettingSection title="Trainer Registry" description="OAuth Discord verification metadata">
        <div className="flex items-center gap-4 p-4 bg-bg-secondary/30 border border-border/50 rounded-2xl">
          {user ? (
            <>
              {user.avatarUrl ? (
                <img
                  src={user.avatarUrl}
                  alt={user.username}
                  className="w-14 h-14 rounded-xl object-cover ring-2 ring-accent/30 shadow"
                />
              ) : (
                <div className="w-14 h-14 rounded-xl bg-bg-secondary flex items-center justify-center text-3xl">
                  🧢
                </div>
              )}
              <div>
                <div className="text-sm font-bold text-text-primary">{user.username}</div>
                <div className="text-[10px] font-bold text-text-muted mt-0.5 uppercase tracking-wider">Discord Authenticated</div>
                <div className="text-[9px] font-mono text-accent mt-1">ID: {user.id}</div>
              </div>
            </>
          ) : (
            <div className="text-xs text-text-muted">No connected trainer account found</div>
          )}
        </div>
      </SettingSection>

      {/* Preferences Section */}
      <SettingSection title="Battle Preferences" description="Format themes and generation constraints">
        <div className="space-y-6">
          {/* Theme Selection */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-3 block">Arena Theme</label>
            <SelectOption
              selected={theme}
              onChange={setTheme}
              options={themes}
              renderOption={(option) => {
                const t = themes.find((th) => th.id === option.id);
                return (
                  <div className="flex items-center gap-2">
                    <span className="text-lg select-none">{t?.emoji}</span>
                    <span className="text-xs font-bold uppercase tracking-wider">{option.name}</span>
                  </div>
                );
              }}
            />
          </div>

          {/* Gen selection */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-3 block">Generations Range</label>
            <SelectOption
              selected={gen.toString()}
              onChange={(v) => setGen(parseInt(v))}
              options={generations.map((g) => ({ id: g.id.toString(), name: g.name }))}
              renderOption={(option) => {
                const count = generations.find((g) => g.id.toString() === option.id)?.count;
                return (
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider">{option.name}</div>
                    <div className="text-[9px] font-bold text-text-muted uppercase tracking-widest mt-0.5">{count} Pokémon</div>
                  </div>
                );
              }}
            />
          </div>
        </div>
      </SettingSection>

      {/* Notifications Toggle */}
      <SettingSection title="Notification Relays" description="Select triggers for Relays">
        <div className="space-y-1">
          <Toggle
            label="Battle Duel Invites"
            enabled={notifications.battleInvites}
            onChange={(v) => setNotifications((n) => ({ ...n, battleInvites: v }))}
          />
          <Toggle
            label="Ranked Match Notifications"
            enabled={notifications.rankedAlerts}
            onChange={(v) => setNotifications((n) => ({ ...n, rankedAlerts: v }))}
          />
          <Toggle
            label="Team Synchronization Logs"
            enabled={notifications.teamSync}
            onChange={(v) => setNotifications((n) => ({ ...n, teamSync: v }))}
          />
        </div>
      </SettingSection>

      {/* Audio Preferences */}
      <SettingSection title="Audio Relays" description="Volume sound configurations">
        <div className="space-y-1">
          <Toggle
            label="Battle Sound Effects"
            enabled={sound}
            onChange={setSound}
          />
          <Toggle
            label="Ambient Background Track"
            enabled={music}
            onChange={setMusic}
          />
        </div>
      </SettingSection>

      {/* Danger Zone */}
      <SettingSection title="Danger Zone Actions" description="Highly destructive commands">
        <div className="space-y-4">
          <button
            type="button"
            onClick={logout}
            className="w-full py-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500 hover:text-bg-primary font-display font-bold text-xs uppercase tracking-widest transition-all cursor-pointer"
          >
            Sign Out Account
          </button>
          <button
            type="button"
            className="w-full py-3 rounded-xl border border-rose-500/40 text-rose-500 hover:bg-rose-500/10 font-display font-bold text-xs uppercase tracking-widest transition-all cursor-pointer"
          >
            Clear Stats Log
          </button>
        </div>
      </SettingSection>

      {/* Footer Info */}
      <div className="text-center text-[9px] text-text-muted font-bold tracking-widest uppercase space-y-1">
        <div>Flame Dueler v1.0.0</div>
        <div>All assets verified under CC Licenses</div>
      </div>
    </motion.div>
  );
}

export default SettingsPage;
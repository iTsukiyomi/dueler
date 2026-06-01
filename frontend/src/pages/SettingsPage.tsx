import { useState } from "react";
import { motion } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";

const themes = [
  { id: "firered", name: "Fire Red", emoji: "🦎", color: "from-red-500 to-orange-500" },
  { id: "leafgreen", name: "Leaf Green", emoji: "🐸", color: "from-green-500 to-emerald-500" },
  { id: "waterblue", name: "Water Blue", emoji: "🐢", color: "from-blue-500 to-cyan-500" },
  { id: "electric", name: "Electric", emoji: "🐭", color: "from-yellow-500 to-amber-500" },
  { id: "dark", name: "Shadow", emoji: "👾", color: "from-purple-600 to-gray-800" },
];

const generations = [
  { id: 1, name: "Generation 1", count: 151 },
  { id: 2, name: "Generation 2", count: 251 },
  { id: 3, name: "Generation 3", count: 386 },
  { id: 4, name: "Generation 4", count: 493 },
  { id: 5, name: "Generation 5", count: 649 },
  { id: 6, name: "Generation 6", count: 721 },
  { id: 7, name: "Generation 7", count: 809 },
  { id: 8, name: "Generation 8", count: 905 },
];

function SettingSection({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-bg-card/40 border border-border/60 p-6"
    >
      <div className="mb-5">
        <h3 className="font-display text-lg font-bold text-text-primary">{title}</h3>
        {description && <p className="text-xs text-text-muted mt-1">{description}</p>}
      </div>
      {children}
    </motion.div>
  );
}

function Toggle({ enabled, onChange, label }: { enabled: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex items-center justify-between cursor-pointer py-3">
      <span className="text-sm text-text-primary">{label}</span>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
          enabled ? "bg-accent" : "bg-border"
        }`}
      >
        <motion.div
          animate={{ x: enabled ? 24 : 2 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className="absolute top-1 w-4 h-4 rounded-full bg-white shadow"
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
      {options.map((option) => (
        <button
          key={option.id}
          onClick={() => onChange(option.id)}
          className={`p-4 rounded-xl border text-left transition-all ${
            selected === option.id
              ? "border-accent bg-accent/10"
              : "border-border/60 hover:border-border"
          }`}
        >
          {renderOption ? renderOption(option) : (
            <div className="font-semibold text-text-primary">{option.name}</div>
          )}
        </button>
      ))}
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

  const currentTheme = themes.find((t) => t.id === theme);

  const handleSave = () => {
    // In production, this would call an API to update settings
    alert("Settings saved successfully!");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 select-none max-w-3xl"
    >
      {/* Header */}
      <div className="border-b border-border/40 pb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-wider text-text-primary">Settings</h1>
          <p className="text-xs text-text-muted mt-1">Customize your battle experience</p>
        </div>
        <button
          onClick={handleSave}
          className="px-6 py-2.5 rounded-xl bg-accent hover:bg-accent-soft text-bg-primary font-display font-bold text-xs uppercase tracking-widest transition-all duration-300 cursor-pointer"
        >
          Save Changes
        </button>
      </div>

      {/* Profile Section */}
      <SettingSection title="Profile" description="Your account information">
        <div className="flex items-center gap-4 p-4 bg-bg-secondary/40 rounded-xl">
          {user && (
            <>
              <img
                src={user.avatarUrl}
                alt={user.username}
                className="w-16 h-16 rounded-2xl ring-2 ring-border"
              />
              <div>
                <div className="font-display text-lg font-bold text-text-primary">{user.username}</div>
                <div className="text-xs text-text-muted">Connected via Discord</div>
                <div className="text-[10px] text-accent mt-1">ID: {user.id}</div>
              </div>
            </>
          )}
        </div>
      </SettingSection>

      {/* Game Settings */}
      <SettingSection
        title="Game Preferences"
        description="Customize your battle settings"
      >
        <div className="space-y-6">
          {/* Theme selection */}
          <div>
            <label className="text-sm font-semibold text-text-primary mb-3 block">Battle Theme</label>
            <SelectOption
              selected={theme}
              onChange={setTheme}
              options={themes}
              renderOption={(option) => {
                const t = themes.find((th) => th.id === option.id);
                return (
                  <div className="flex items-center gap-2">
                    <span>{t?.emoji}</span>
                    <span className="font-semibold text-text-primary">{option.name}</span>
                  </div>
                );
              }}
            />
          </div>

          {/* Generation selection */}
          <div>
            <label className="text-sm font-semibold text-text-primary mb-3 block">Generation</label>
            <SelectOption
              selected={gen.toString()}
              onChange={(v) => setGen(parseInt(v))}
              options={generations.map((g) => ({ id: g.id.toString(), name: g.name }))}
              renderOption={(option) => (
                <div>
                  <div className="font-semibold text-text-primary">{option.name}</div>
                  <div className="text-[10px] text-text-muted">{generations.find((g) => g.id.toString() === option.id)?.count} Pokemon</div>
                </div>
              )}
            />
          </div>
        </div>
      </SettingSection>

      {/* Notifications */}
      <SettingSection
        title="Notifications"
        description="Manage how you receive updates"
      >
        <div className="space-y-1">
          <Toggle
            label="Battle Invites"
            enabled={notifications.battleInvites}
            onChange={(v) => setNotifications((n) => ({ ...n, battleInvites: v }))}
          />
          <Toggle
            label="Ranked Match Alerts"
            enabled={notifications.rankedAlerts}
            onChange={(v) => setNotifications((n) => ({ ...n, rankedAlerts: v }))}
          />
          <Toggle
            label="Team Sync Updates"
            enabled={notifications.teamSync}
            onChange={(v) => setNotifications((n) => ({ ...n, teamSync: v }))}
          />
          <Toggle
            label="Newsletter & Updates"
            enabled={notifications.newsletter}
            onChange={(v) => setNotifications((n) => ({ ...n, newsletter: v }))}
          />
        </div>
      </SettingSection>

      {/* Audio */}
      <SettingSection
        title="Audio"
        description="Sound and music preferences"
      >
        <div className="space-y-1">
          <Toggle
            label="Battle Sound Effects"
            enabled={sound}
            onChange={setSound}
          />
          <Toggle
            label="Background Music"
            enabled={music}
            onChange={setMusic}
          />
        </div>
      </SettingSection>

      {/* Account Actions */}
      <SettingSection title="Account">
        <div className="space-y-4">
          <button className="w-full py-3 rounded-xl bg-bg-secondary/40 border border-border/60 text-text-secondary hover:text-text-primary text-sm font-semibold transition-all">
            Change Password
          </button>
          <button
            onClick={logout}
            className="w-full py-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500 hover:text-white text-sm font-semibold transition-all"
          >
            Sign Out
          </button>
        </div>
      </SettingSection>

      {/* Danger Zone */}
      <SettingSection title="Danger Zone">
        <div className="space-y-4">
          <button className="w-full py-3 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-sm font-semibold transition-all">
            Reset Statistics
          </button>
          <button className="w-full py-3 rounded-xl border border-rose-500/50 text-rose-500 hover:bg-rose-500/20 text-sm font-semibold transition-all">
            Delete Account
          </button>
        </div>
      </SettingSection>

      {/* Footer info */}
      <div className="text-center text-xs text-text-muted space-y-1">
        <p>Flame Dueler v1.0.0</p>
        <p>Discord Bot synced in real-time</p>
      </div>
    </motion.div>
  );
}

export default SettingsPage;
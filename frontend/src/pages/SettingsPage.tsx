import { useState } from "react";
import { motion } from "framer-motion";
import { usePlayerProfile } from "../hooks/usePokemonData";
import { useAuthStore } from "../stores/authStore";
import toast from "react-hot-toast";
import { 
  Flame, 
  Leaf, 
  Droplet, 
  Zap, 
  Moon, 
  User, 
  LogOut, 
  Trash2, 
  Save, 
  Settings, 
  Bell, 
  Volume2, 
  Music,
  Swords,
  Trophy,
  RefreshCw,
  Database,
  ShieldAlert
} from "lucide-react";

const themes = [
  { id: "firered", name: "Fire Red", icon: Flame, color: "var(--poke-red)", description: "Crimson battle grid" },
  { id: "leafgreen", name: "Leaf Green", icon: Leaf, color: "#10b981", description: "Viridian solar grid" },
  { id: "waterblue", name: "Water Blue", icon: Droplet, color: "var(--poke-blue)", description: "Cerulean current grid" },
  { id: "electric", name: "Electric", icon: Zap, color: "var(--poke-yellow)", description: "Vermilion dynamo grid" },
  { id: "dark", name: "Shadow", icon: Moon, color: "#a855f7", description: "Lavender ghost grid" },
];

const generations = [
  { id: "1", name: "Gen 1", description: "151 Pokémon · Kanto", color: "var(--poke-blue)" },
  { id: "2", name: "Gen 2", description: "251 Pokémon · Johto", color: "var(--poke-blue)" },
  { id: "3", name: "Gen 3", description: "386 Pokémon · Hoenn", color: "var(--poke-blue)" },
  { id: "4", name: "Gen 4", description: "493 Pokémon · Sinnoh", color: "var(--poke-blue)" },
  { id: "5", name: "Gen 5", description: "649 Pokémon · Unova", color: "var(--poke-blue)" },
  { id: "6", name: "Gen 6", description: "721 Pokémon · Kalos", color: "var(--poke-blue)" },
  { id: "7", name: "Gen 7", description: "809 Pokémon · Alola", color: "var(--poke-blue)" },
  { id: "8", name: "Gen 8", description: "905 Pokémon · Galar", color: "var(--poke-blue)" },
];

function SettingSection({ title, description, children, icon: Icon }: { title: string; description?: string; children: React.ReactNode; icon?: any }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6 overflow-hidden relative group"
    >
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h3 className="font-display text-sm font-black text-text-primary tracking-wider uppercase flex items-center gap-2">
            {Icon && <Icon className="w-4.5 h-4.5 text-[var(--poke-yellow)]" />}
            <span>{title}</span>
          </h3>
          {description && <p className="text-[9px] font-bold text-text-muted mt-1 uppercase tracking-wider font-mono">{description}</p>}
        </div>
      </div>
      {children}
    </motion.div>
  );
}

function Toggle({ enabled, onChange, label, icon: Icon }: { enabled: boolean; onChange: (v: boolean) => void; label: string; icon?: any }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b border-[var(--border-subtle)] last:border-0 select-none">
      <div className="flex items-center gap-3">
        {Icon && <Icon className="w-4 h-4 text-text-muted" />}
        <span className="text-xs font-bold text-text-secondary uppercase tracking-wider font-display">{label}</span>
      </div>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`relative w-14 h-7 border transition-all duration-200 cursor-pointer overflow-hidden ${
          enabled 
            ? "border-[var(--poke-blue)] bg-[rgba(0,191,255,0.06)] text-[var(--poke-blue)] shadow-[0_0_10px_rgba(0,191,255,0.15)]" 
            : "border-[var(--border-default)] bg-[var(--bg-raised)] text-text-muted"
        }`}
        style={{ borderRadius: "var(--radius-sm)" }}
      >
        <div className="absolute inset-0 flex items-center justify-between px-2 font-mono text-[8px] font-bold uppercase tracking-wider">
          <span className={enabled ? "text-[var(--poke-blue)]" : "opacity-20"}>ON</span>
          <span className={!enabled ? "text-text-muted" : "opacity-20"}>OFF</span>
        </div>
        <motion.div
          animate={{ x: enabled ? 34 : 2 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className={`absolute top-1 w-4 h-[18px] border transition-colors ${
            enabled ? "bg-[var(--poke-blue)] border-[var(--poke-blue)]" : "bg-text-muted border-text-muted"
          }`}
          style={{ borderRadius: "1px" }}
        />
      </button>
    </div>
  );
}

function CustomSelectList<T extends { id: string; name: string; description?: string; icon?: any; color?: string }>({
  selected,
  onChange,
  options
}: {
  selected: string;
  onChange: (id: string) => void;
  options: T[];
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {options.map((option) => {
        const isSelected = selected === option.id;
        const Icon = option.icon;
        
        return (
          <button
            type="button"
            key={option.id}
            onClick={() => onChange(option.id)}
            className={`flex items-center justify-between p-3.5 border transition-all duration-200 cursor-pointer ${
              isSelected 
                ? "border-[var(--poke-blue)] bg-[rgba(0,191,255,0.06)] text-text-primary shadow-[0_0_12px_rgba(0,191,255,0.12)]" 
                : "border-[var(--border-default)] bg-[var(--bg-raised)] text-text-secondary hover:border-[var(--border-bright)] hover:bg-[var(--bg-float)]"
            }`}
            style={{ borderRadius: "var(--radius-lg)" }}
          >
            <div className="flex items-center gap-3">
              <div 
                className="w-1 h-6 rounded" 
                style={{ backgroundColor: option.color || "var(--border-default)" }}
              />
              <div className="flex flex-col items-start text-left">
                <span className={`text-xs font-bold uppercase tracking-wider font-display ${isSelected ? "text-[var(--poke-blue)]" : "text-text-primary"}`}>
                  {option.name}
                </span>
                {option.description && (
                  <span className="text-[9px] text-text-muted mt-0.5 uppercase tracking-widest font-mono">
                    {option.description}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2 shrink-0">
              {Icon && (
                <Icon 
                  className="w-4 h-4 transition-colors" 
                  style={{ color: isSelected ? (option.color || "var(--poke-blue)") : "var(--text-muted)" }} 
                />
              )}
              {isSelected ? (
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--poke-blue)] animate-pulse" />
              ) : null}
            </div>
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
      <div className="border-b border-[var(--border-subtle)] pb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-[9px] font-mono text-text-muted uppercase tracking-widest mb-1">
            <span>Control Room</span>
            <span>/</span>
            <span className="text-text-secondary">OS Configuration</span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-wider text-text-primary uppercase flex items-center gap-3">
            <Settings className="w-7 h-7 text-[var(--poke-blue)]" />
            <span>Settings</span>
          </h1>
          <p className="text-xs text-text-muted mt-1 font-medium font-sans">Configure league attributes and trainer preferences</p>
        </div>
        <button
          onClick={handleSave}
          className="btn-primary"
        >
          <Save className="w-4 h-4" />
          <span>Save Changes</span>
        </button>
      </div>

      {/* Account Info Section */}
      <SettingSection title="Trainer Registry" description="OAuth Discord verification metadata" icon={User}>
        <div className="flex items-center gap-4 p-4 bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
          {user ? (
            <>
              {user.avatarUrl ? (
                <img
                  src={user.avatarUrl}
                  alt={user.username}
                  className="w-14 h-14 object-cover ring-2 ring-[var(--poke-yellow)] shadow"
                  style={{ borderRadius: "var(--radius-lg)" }}
                />
              ) : (
                <div 
                  className="w-14 h-14 bg-[var(--bg-secondary)] flex items-center justify-center border border-[var(--border-default)]"
                  style={{ borderRadius: "var(--radius-lg)" }}
                >
                  <User className="w-6 h-6 text-text-muted" />
                </div>
              )}
              <div>
                <div className="text-sm font-bold text-text-primary font-display uppercase tracking-wide">{user.username}</div>
                <div className="text-[9px] font-mono text-text-muted mt-0.5 uppercase tracking-wider">Discord Authenticated</div>
                <div className="text-[9px] font-mono text-[var(--poke-yellow)] mt-1">ID: {user.id}</div>
              </div>
            </>
          ) : (
            <div className="text-xs text-text-muted font-display uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-text-danger" />
              <span>No connected trainer account found</span>
            </div>
          )}
        </div>
      </SettingSection>

      {/* Preferences Section */}
      <SettingSection title="Battle Preferences" description="Format themes and generation constraints" icon={Settings}>
        <div className="space-y-6">
          {/* Theme Selection */}
          <div>
            <label className="text-[9px] font-mono font-bold uppercase tracking-widest text-text-muted mb-3 block">Arena Theme</label>
            <CustomSelectList
              selected={theme}
              onChange={setTheme}
              options={themes}
            />
          </div>

          {/* Gen selection */}
          <div>
            <label className="text-[9px] font-mono font-bold uppercase tracking-widest text-text-muted mb-3 block">Generations Range</label>
            <CustomSelectList
              selected={gen.toString()}
              onChange={(v) => setGen(parseInt(v))}
              options={generations}
            />
          </div>
        </div>
      </SettingSection>

      {/* Notifications Toggle */}
      <SettingSection title="Notification Relays" description="Select triggers for Relays" icon={Bell}>
        <div className="space-y-1">
          <Toggle
            label="Battle Duel Invites"
            icon={Swords}
            enabled={notifications.battleInvites}
            onChange={(v) => setNotifications((n) => ({ ...n, battleInvites: v }))}
          />
          <Toggle
            label="Ranked Match Notifications"
            icon={Trophy}
            enabled={notifications.rankedAlerts}
            onChange={(v) => setNotifications((n) => ({ ...n, rankedAlerts: v }))}
          />
          <Toggle
            label="Team Synchronization Logs"
            icon={RefreshCw}
            enabled={notifications.teamSync}
            onChange={(v) => setNotifications((n) => ({ ...n, teamSync: v }))}
          />
        </div>
      </SettingSection>

      {/* Audio Preferences */}
      <SettingSection title="Audio Relays" description="Volume sound configurations" icon={Volume2}>
        <div className="space-y-1">
          <Toggle
            label="Battle Sound Effects"
            icon={Volume2}
            enabled={sound}
            onChange={setSound}
          />
          <Toggle
            label="Ambient Background Track"
            icon={Music}
            enabled={music}
            onChange={setMusic}
          />
        </div>
      </SettingSection>

      {/* Danger Zone */}
      <SettingSection title="Danger Zone Actions" description="Highly destructive commands" icon={ShieldAlert}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            type="button"
            onClick={logout}
            className="btn-danger w-full flex items-center justify-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out Account</span>
          </button>
          <button
            type="button"
            className="btn-secondary w-full flex items-center justify-center gap-2 border-red-500/40 hover:border-red-500/80 hover:bg-red-500/10 text-red-500"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Stats Log</span>
          </button>
        </div>
      </SettingSection>

      {/* Footer Info */}
      <div className="text-center text-[9px] text-text-muted font-bold tracking-widest uppercase space-y-1 font-mono pt-4">
        <div>Flame Dueler v1.0.0</div>
        <div>All assets verified under CC Licenses</div>
      </div>
    </motion.div>
  );
}

export default SettingsPage;
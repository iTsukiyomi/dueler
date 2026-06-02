import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";
import toast from "react-hot-toast";
import { PokeDexScan } from "../pokemon/PokeDexScan";
import { Search, User, LogOut, Terminal, ShieldAlert } from "lucide-react";

interface ManifestPokemon {
  id: number;
  name: string;
  types: string[];
}

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuthStore();
  const { data: profile } = usePlayerProfile();
  const navigate = useNavigate();

  // Search states
  const [searchQuery, setSearchQuery] = useState("");
  const [pokemonList, setPokemonList] = useState<ManifestPokemon[]>([]);
  const [searchResults, setSearchResults] = useState<ManifestPokemon[]>([]);
  const [searchFocused, setSearchFocused] = useState(false);
  const [activeScanName, setActiveScanName] = useState<string | null>(null);

  // Dropdown states
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  // Fetch manifest client-side for rapid search
  useEffect(() => {
    fetch("/pokemon-icons/manifest.json")
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Failed to load manifest");
      })
      .then((data) => {
        if (data && data.pokemon) {
          setPokemonList(data.pokemon);
        }
      })
      .catch((err) => console.error("Error loading Pokémon search list:", err));
  }, []);

  // Filter search results
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const query = searchQuery.toLowerCase().trim();
    const filtered = pokemonList
      .filter((p) => p.name.toLowerCase().includes(query) || p.types.some((t) => t.toLowerCase() === query))
      .slice(0, 6);
    setSearchResults(filtered);
  }, [searchQuery, pokemonList]);

  // Click outside handlers
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchFocused(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Hotkey "/" for search focus
  useEffect(() => {
    const handleHotkey = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        const input = searchRef.current?.querySelector("input");
        input?.focus();
      }
    };
    window.addEventListener("keydown", handleHotkey);
    return () => window.removeEventListener("keydown", handleHotkey);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      setProfileDropdownOpen(false);
      toast.success("Trainer logged out successfully");
      navigate("/");
    } catch {
      toast.error("Failed to terminate session");
    }
  };

  const handleDiscordLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <>
      <nav className="navbar select-none">
        {/* Left Side: Monospace Navigation Node/Breadcrumb */}
        <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted uppercase tracking-widest">
          <Terminal className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-text-secondary">Silph OS</span>
          <span>/</span>
          <span className="text-[var(--poke-blue)]">Terminal Link</span>
        </div>

        {/* Center: Search Bar */}
        <div className="flex-1 flex justify-center items-center px-4">
          <div ref={searchRef} className="relative w-full max-w-[320px]">
            <div className="search-bar">
              <Search className="w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                placeholder="Search database..."
                className="bg-transparent text-text-primary font-sans text-xs outline-none w-full"
              />
              <span className="mono text-[8px] bg-[var(--bg-overlay)] border border-[var(--border-default)] text-text-muted px-1.5 py-0.5 rounded">
                /
              </span>
            </div>

            {/* Search results dropdown */}
            <AnimatePresence>
              {searchFocused && searchResults.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.12 }}
                  className="absolute left-0 right-0 mt-2 bg-[var(--bg-float)] border border-[var(--border-bright)] rounded-[var(--radius-md)] shadow-2xl p-2 z-float max-h-80 overflow-y-auto"
                >
                  <div className="mono text-[8px] text-text-muted uppercase tracking-widest px-3 py-1 pb-2 border-b border-[var(--border-default)] mb-1.5">
                    Query Matches
                  </div>
                  {searchResults.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => {
                        setActiveScanName(p.name);
                        setSearchQuery("");
                        setSearchFocused(false);
                      }}
                      className="flex items-center justify-between p-2 rounded hover:bg-[var(--bg-overlay)] cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <img
                          src={`/pokemon-icons/${p.id}.png`}
                          alt=""
                          className="w-8 h-8 object-contain"
                          style={{ imageRendering: "pixelated" }}
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%233D5068'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3C/svg%3E";
                          }}
                        />
                        <span className="font-rajdhani text-sm font-bold text-text-primary uppercase tracking-wide">
                          {p.name.replace("-", " ")}
                        </span>
                      </div>
                      <div className="flex gap-1">
                        {p.types.map((type) => (
                          <span
                            key={type}
                            className="text-[8px] uppercase tracking-wider font-semibold border border-[var(--border-default)] rounded px-1.5 py-0.5 text-text-secondary bg-[var(--bg-raised)]"
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Right Side: Auth Menu */}
        <div className="flex items-center gap-4 shrink-0">
          {isAuthenticated && user ? (
            <div ref={profileRef} className="relative">
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2.5 px-3 py-1.5 rounded-[var(--radius-md)] bg-[var(--bg-raised)] border border-[var(--border-default)] hover:border-[var(--border-bright)] transition-all cursor-pointer select-none"
              >
                <div className="relative">
                  {user.avatarUrl ? (
                    <img
                      src={user.avatarUrl}
                      alt={user.username}
                      className="w-6 h-6 rounded-full object-cover shadow-md"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center text-xs border border-[var(--border-default)]">
                      <User className="w-3.5 h-3.5 text-text-muted" />
                    </div>
                  )}
                  {/* Status dot */}
                  <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-[#10b981] border-2 border-bg-base" />
                </div>
                <span className="hidden md:inline font-sans text-xs font-semibold text-text-primary">
                  {user.username}
                </span>
                <span className="text-text-muted text-xs">▾</span>
              </button>

              {/* Profile dropdown container */}
              <AnimatePresence>
                {profileDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.12 }}
                    className="absolute right-0 mt-2 w-52 bg-[var(--bg-float)] border border-[var(--border-bright)] rounded-[var(--radius-md)] shadow-2xl p-1.5 z-float flex flex-col"
                  >
                    <div className="flex items-center gap-3 p-3 pb-2 border-b border-[var(--border-default)] mb-1.5">
                      {user.avatarUrl ? (
                        <img
                          src={user.avatarUrl}
                          alt=""
                          className="w-8 h-8 rounded object-cover border border-[var(--border-default)]"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded bg-[var(--bg-overlay)] flex items-center justify-center border border-[var(--border-default)]">
                          <User className="w-4 h-4 text-text-muted" />
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="font-display text-[10px] font-black text-text-primary uppercase tracking-wide truncate">
                          {user.username}
                        </div>
                        {profile && (
                          <div className="mono text-[9px] text-[var(--poke-yellow)] mt-0.5">
                            {profile.elo} ELO
                          </div>
                        )}
                      </div>
                    </div>

                    <Link
                      to="/dashboard"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="dropdown-item"
                    >
                      <User className="w-4 h-4 text-text-secondary" />
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">Profile Center</span>
                    </Link>
                    <Link
                      to="/dashboard/settings"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="dropdown-item"
                    >
                      <Terminal className="w-4 h-4 text-text-secondary" />
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">OS Config</span>
                    </Link>

                    {/* Divider */}
                    <div className="h-px bg-[var(--border-default)] my-1" />

                    <button
                      onClick={handleLogout}
                      className="dropdown-item text-text-danger hover:bg-red-500/10"
                    >
                      <LogOut className="w-4 h-4 text-[var(--poke-red)]" />
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">Disconnect</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <button
              onClick={handleDiscordLogin}
              className="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-md)] border border-[#5865F2]/75 text-[#5865F2] hover:bg-[#5865F2]/10 hover:text-white transition-all text-xs font-bold uppercase tracking-wider font-rajdhani cursor-pointer"
            >
              <span>Login with Discord</span>
            </button>
          )}
        </div>
      </nav>

      {/* Global scan viewer */}
      <PokeDexScan
        pokemonName={activeScanName}
        onClose={() => setActiveScanName(null)}
      />
    </>
  );
}

export default Navbar;
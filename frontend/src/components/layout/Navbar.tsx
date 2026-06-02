import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { usePlayerProfile } from "../../hooks/usePokemonData";
import toast from "react-hot-toast";
import { PokeDexScan } from "../pokemon/PokeDexScan";

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
        {/* Logo Zone (Left) */}
        <Link to="/dashboard" className="flex items-center gap-3 shrink-0 group">
          <div className="relative w-8 h-8 rounded-full border border-border-default bg-bg-raised flex items-center justify-center overflow-hidden">
            {/* Poké Ball outline structure */}
            <svg width="18" height="18" viewBox="0 0 32 32" className="text-text-secondary group-hover:text-poke-red transition-colors duration-200">
              <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M 3.05 16 A 13 13 0 0 1 28.95 16 Z" fill="currentColor" opacity="0.25" />
              <line x1="2" y1="16" x2="30" y2="16" stroke="currentColor" strokeWidth="2" />
              <circle cx="16" cy="16" r="4.5" fill="var(--bg-raised)" stroke="currentColor" strokeWidth="2" />
            </svg>
            {/* Spark animation ring on hover */}
            <span className="absolute inset-0 border border-poke-blue opacity-0 scale-75 group-hover:scale-100 group-hover:opacity-40 transition-all duration-300 rounded-full" />
          </div>
          <div className="flex flex-col">
            <span className="font-display text-xs font-black text-text-primary tracking-widest leading-none">
              POKÉBOT
            </span>
            <span className="mono text-[8px] text-text-muted mt-0.5 uppercase tracking-wider">
              Silph OS v1.0
            </span>
          </div>
        </Link>

        {/* Spacer & Search (Center) */}
        <div className="flex-1 flex justify-center items-center px-4">
          <div ref={searchRef} className="relative z-raised">
            <div className="search-bar">
              {/* magnifying glass in Pokédex style */}
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className="text-text-muted"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                placeholder="Search Pokémon or type..."
                className="bg-transparent text-text-primary font-sans text-xs outline-none w-44 md:w-56 focus:w-64 transition-all duration-300"
              />
              <span className="mono text-[8px] bg-bg-overlay border border-border-subtle text-text-muted px-1.5 py-0.5 rounded">
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
                  transition={{ duration: 0.15 }}
                  className="absolute left-0 right-0 mt-2 bg-bg-float border border-border-default rounded-lg shadow-2xl p-2 z-float max-h-80 overflow-y-auto"
                >
                  <div className="mono text-[8px] text-text-muted uppercase tracking-widest px-3 py-1 pb-2 border-b border-border-subtle mb-1.5">
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
                      className="flex items-center justify-between p-2 rounded-md hover:bg-bg-overlay cursor-pointer transition-colors"
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
                            className="text-[8px] uppercase tracking-wider font-semibold border border-border-subtle rounded px-1 text-text-secondary"
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

        {/* Right Auth Zone */}
        <div className="flex items-center gap-4 shrink-0">
          {isAuthenticated && user ? (
            /* State B: Logged In */
            <div ref={profileRef} className="relative">
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-bg-raised border border-border-default hover:border-border-bright hover:bg-bg-float transition-all cursor-pointer select-none"
              >
                <div className="relative">
                  {user.avatarUrl ? (
                    <img
                      src={user.avatarUrl}
                      alt={user.username}
                      className="w-7 h-7 rounded-full object-cover ring-2 ring-poke-yellow shadow-md"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-bg-overlay flex items-center justify-center text-sm border border-poke-yellow">
                      🧢
                    </div>
                  )}
                  {/* Status dot */}
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#57F287] border-2 border-bg-base" />
                </div>
                <span className="hidden md:inline font-sans text-xs font-semibold text-text-primary">
                  {user.username}
                </span>
                <span className="caret text-xs">▾</span>
              </button>

              {/* Profile dropdown container */}
              <AnimatePresence>
                {profileDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-56 bg-bg-float border border-border-default rounded-lg shadow-2xl p-2 z-float flex flex-col"
                  >
                    <div className="flex items-center gap-3 p-3 pb-2 border-b border-border-subtle mb-1.5">
                      {user.avatarUrl ? (
                        <img
                          src={user.avatarUrl}
                          alt=""
                          className="w-10 h-10 rounded-lg object-cover border border-poke-yellow"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-bg-overlay flex items-center justify-center text-lg border border-poke-yellow">
                          🧢
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="font-display text-[10px] font-black text-text-primary uppercase tracking-wide truncate">
                          {user.username}
                        </div>
                        {profile && (
                          <div className="mono text-[9px] text-text-brand mt-0.5">
                            {profile.elo} ELO Rating
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Nav Items */}
                    <Link
                      to="/dashboard"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="dropdown-item"
                    >
                      <svg className="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">Profile Center</span>
                    </Link>
                    <Link
                      to="/dashboard/settings"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="dropdown-item"
                    >
                      <svg className="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">OS Configuration</span>
                    </Link>

                    {/* Divider */}
                    <div className="h-px bg-border-subtle my-1" />

                    {/* Logout */}
                    <button
                      onClick={handleLogout}
                      className="dropdown-item text-text-danger hover:bg-poke-red/10 rounded-md"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      <span className="font-rajdhani font-semibold uppercase tracking-wider text-xs">Terminate Hook</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            /* State A: Logged Out */
            <button
              onClick={handleDiscordLogin}
              className="flex items-center gap-2 px-4 py-2.5 rounded border border-[#5865F2]/70 text-[#5865F2] hover:bg-[#5865F2]/10 hover:text-white transition-all duration-200 text-xs font-bold uppercase tracking-wider font-rajdhani cursor-pointer"
            >
              <span>⊙</span>
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
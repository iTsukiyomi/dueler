import React, { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useTeamStore } from '@/stores/teamStore';
import { BentoItem } from '@/components/ui/cybernetic-bento-grid';
import { Swords, Trophy, Coins, Settings2, Sparkles, User, Link2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ProfilePage() {
  const { user, profile, fetchProfile, isProfileLoading } = useAuthStore();
  const { teams, fetchTeams } = useTeamStore();

  useEffect(() => {
    fetchProfile();
    fetchTeams();
  }, [fetchProfile, fetchTeams]);

  // Calculations
  const wins = profile?.wins ?? 0;
  const losses = profile?.losses ?? 0;
  const totalGames = wins + losses;
  const winRate = totalGames > 0 ? ((wins / totalGames) * 100).toFixed(1) : '0.0';

  // Find active team details
  const activeTeamSummary = teams.find((t) => t.is_active);

  return (
    <div className="w-full text-slate-100 min-h-screen pb-12">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Profile Welcome Header */}
        <div className="flex flex-col sm:flex-row items-center gap-6 bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl backdrop-blur-md">
          <div className="relative size-24 rounded-full overflow-hidden border-2 border-orange-500 shadow-lg shadow-orange-500/20 shrink-0">
            <img 
              src={user?.avatarUrl} 
              alt={user?.username} 
              className="size-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || 'Trainer'}`;
              }}
            />
          </div>
          <div className="text-center sm:text-left grow space-y-2">
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 to-slate-300">
                Welcome back, {user?.username || 'Trainer'}!
              </h1>
              <Sparkles className="size-5 text-orange-400 animate-pulse hidden sm:block" />
            </div>
            <p className="text-slate-400 text-sm max-w-xl">
              Ready to climb the ladder? Adjust your squad, test new strategies in the chat, or check the leaderboard to see who's dominating.
            </p>
          </div>
          <div className="flex flex-col gap-2 shrink-0 w-full sm:w-auto">
            <Link 
              to="/dashboard/teams" 
              className="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white font-bold text-sm px-5 py-2.5 rounded-xl transition shadow-lg shadow-orange-600/15"
            >
              <Swords className="size-4" />
              Manage Squads
            </Link>
          </div>
        </div>

        {/* Cybernetic Bento Grid for Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* ELO Card */}
          <BentoItem className="flex flex-col justify-between p-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-widest text-orange-400">Trainer Rating</span>
                <h3 className="text-5xl font-extrabold mt-2 tracking-tight text-white">{profile?.elo ?? 1000}</h3>
              </div>
              <div className="size-10 rounded-lg bg-orange-500/10 border border-orange-500/25 flex items-center justify-center text-orange-400">
                <Trophy className="size-5" />
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-slate-900/60 flex justify-between items-center text-sm text-slate-400">
              <span>Ladder Rank</span>
              <span className="font-semibold text-slate-200">
                {profile?.rank ? `#${profile.rank}` : 'Unranked'}
              </span>
            </div>
          </BentoItem>

          {/* Win/Loss Card */}
          <BentoItem className="flex flex-col justify-between p-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-widest text-red-400">Battle Stats</span>
                <h3 className="text-4xl font-extrabold mt-2 tracking-tight text-white">
                  {wins}W <span className="text-slate-500">/</span> {losses}L
                </h3>
              </div>
              <div className="size-10 rounded-lg bg-red-500/10 border border-red-500/25 flex items-center justify-center text-red-400">
                <Swords className="size-5" />
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-slate-900/60 flex justify-between items-center text-sm text-slate-400">
              <span>Win Ratio</span>
              <span className="font-semibold text-slate-200">{winRate}%</span>
            </div>
          </BentoItem>

          {/* Wallet/Inventory */}
          <BentoItem className="flex flex-col justify-between p-6">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-widest text-yellow-400">Trainer Wallet</span>
                <h3 className="text-5xl font-extrabold mt-2 tracking-tight text-white">{profile?.wallet ?? 0}</h3>
              </div>
              <div className="size-10 rounded-lg bg-yellow-500/10 border border-yellow-500/25 flex items-center justify-center text-yellow-400">
                <Coins className="size-5" />
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-slate-900/60 flex justify-between items-center text-sm text-slate-400">
              <span>Active Currency</span>
              <span className="font-semibold text-slate-200">Pokécoins</span>
            </div>
          </BentoItem>
        </div>

        {/* Main Details and Active Squad Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Squad Display */}
          <div className="lg:col-span-2 bg-slate-900/25 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md space-y-6">
            <div className="flex justify-between items-center border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-200">Active Squad</h2>
                <p className="text-slate-400 text-xs mt-1">This squad will represent you in Discord PvP battles</p>
              </div>
              {activeTeamSummary ? (
                <span className="text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2.5 py-1 rounded-md">
                  {activeTeamSummary.name}
                </span>
              ) : (
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-800/40 px-2.5 py-1 rounded-md">
                  None Active
                </span>
              )}
            </div>

            {activeTeamSummary && activeTeamSummary.pokemon && activeTeamSummary.pokemon.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {activeTeamSummary.pokemon.map((p, idx) => (
                  <div 
                    key={idx} 
                    className="relative flex flex-col items-center bg-slate-950/60 border border-slate-850 p-4 rounded-xl group transition hover:border-orange-500/30 overflow-hidden"
                  >
                    {p.shiny && (
                      <div className="absolute top-2 right-2 text-xs font-bold text-yellow-500 flex items-center gap-0.5 select-none bg-yellow-500/10 border border-yellow-500/25 rounded px-1.5 py-0.2 scale-90">
                        ✨ SHINY
                      </div>
                    )}
                    <img 
                      src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${p.shiny ? 'shiny/' : ''}${p.pokemon_id}.png`} 
                      alt={p.pokname} 
                      className="size-20 object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.4)] group-hover:scale-110 transition duration-300"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png';
                      }}
                    />
                    <span className="text-sm font-bold text-slate-200 capitalize mt-2 truncate w-full text-center">
                      {p.pokname.replace(/-/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl space-y-4">
                <div className="size-12 rounded-full bg-slate-900 flex items-center justify-center border border-slate-800">
                  <Swords className="size-5 text-slate-400" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-400">No active squad selected</h4>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm">Go to My Squads, choose a squad, and click 'Activate' to use it in Discord battles.</p>
                </div>
                <Link 
                  to="/dashboard/teams" 
                  className="text-xs font-bold text-orange-400 hover:text-orange-300 underline"
                >
                  Go select a squad
                </Link>
              </div>
            )}
          </div>

          {/* Quick Config / Info */}
          <div className="bg-slate-900/25 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md flex flex-col justify-between space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
                <Settings2 className="size-5 text-slate-400" />
                Battle Parameters
              </h2>
              <div className="space-y-4 text-sm">
                <div className="flex justify-between items-center py-2.5 border-b border-slate-900/60">
                  <span className="text-slate-400">Battle Generation</span>
                  <span className="font-bold text-orange-400">Gen {profile?.gen ?? 5}</span>
                </div>
                <div className="flex justify-between items-center py-2.5 border-b border-slate-900/60">
                  <span className="text-slate-400">Theme</span>
                  <span className="font-bold text-slate-200 capitalize">{profile?.theme ?? 'firered'}</span>
                </div>
                <div className="flex justify-between items-center py-2.5 border-b border-slate-900/60">
                  <span className="text-slate-400">Shiny Lock</span>
                  <span className="font-bold text-green-500">Unlocked</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-900 space-y-2">
              <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Discord Integration</span>
              <p className="text-xs text-slate-400 leading-relaxed">
                Connect the bot to your Discord servers. Type <code className="text-orange-400 font-mono bg-slate-900 px-1 py-0.5 rounded">/battle</code> to fight or <code className="text-orange-400 font-mono bg-slate-900 px-1 py-0.5 rounded">/party</code> to show your active team!
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

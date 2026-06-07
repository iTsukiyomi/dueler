import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/api/client';
import { Trophy, Medal, Star, Swords, RefreshCw } from 'lucide-react';

interface LeaderboardUser {
  rank: number;
  id: string;
  username: string;
  avatarUrl: string;
  elo: number;
  wins: number;
  losses: number;
  winRate: number;
}

interface LeaderboardResponse {
  leaderboard: LeaderboardUser[];
  updatedAt: string;
}

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [updatedAt, setUpdatedAt] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadLeaderboard = () => {
    setLoading(true);
    apiFetch<LeaderboardResponse>('/api/leaderboard')
      .then((res) => {
        setLeaderboard(res.leaderboard || []);
        if (res.updatedAt) {
          setUpdatedAt(new Date(res.updatedAt).toLocaleTimeString());
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load leaderboard');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadLeaderboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-100">
        <div className="relative size-12">
          <div className="absolute inset-0 rounded-full border-4 border-orange-500/20 animate-pulse" />
          <div className="absolute inset-0 rounded-full border-4 border-t-orange-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/15 border border-red-500/30 text-red-400 p-6 rounded-2xl max-w-lg mx-auto text-center mt-12 space-y-4">
        <p className="font-semibold">{error}</p>
        <button 
          onClick={loadLeaderboard}
          className="bg-slate-800 text-slate-200 border border-slate-700 px-4 py-2 rounded-xl text-xs font-bold"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Split top 3 and others
  const topThree = leaderboard.slice(0, 3);
  const restOfList = leaderboard.slice(3);

  return (
    <div className="w-full text-slate-100 min-h-screen pb-12">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/20 p-5 rounded-2xl border border-slate-800/60 backdrop-blur-md">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
              <Trophy className="size-6 text-yellow-500" />
              Global Leaderboard
            </h1>
            <p className="text-slate-400 text-xs mt-0.5">
              The highest rated trainers on Flame Dueler. {updatedAt && `Last updated: ${updatedAt}`}
            </p>
          </div>
          <button
            onClick={loadLeaderboard}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs px-4 py-2.5 rounded-xl transition border border-slate-700 shrink-0"
          >
            <RefreshCw className="size-3.5" />
            Refresh Standing
          </button>
        </div>

        {/* Podium for Top 3 */}
        {topThree.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-end py-4">
            
            {/* Rank 2 - Left */}
            {topThree[1] && (
              <div className="bg-slate-900/30 border border-slate-850/60 rounded-2xl p-6 text-center space-y-4 backdrop-blur-md order-2 sm:order-1 sm:h-[230px] flex flex-col justify-end relative overflow-hidden">
                <div className="absolute top-0 inset-x-0 h-1 bg-slate-400" />
                <div className="relative size-16 mx-auto rounded-full overflow-hidden border-2 border-slate-400 shadow-lg shadow-slate-400/10">
                  <img 
                    src={topThree[1].avatarUrl || `https://cdn.discordapp.com/embed/avatars/${(parseInt(topThree[1].id) || 0) % 5}.png`} 
                    alt={topThree[1].username}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${topThree[1].username}`;
                    }}
                  />
                </div>
                <div>
                  <h3 className="font-bold text-slate-200 truncate">{topThree[1].username}</h3>
                  <p className="text-xs text-slate-500 font-semibold uppercase tracking-widest mt-1">2nd Place</p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-900 pt-3">
                  <span className="font-mono">{topThree[1].elo} ELO</span>
                  <span className="font-semibold text-slate-300">{topThree[1].winRate}% Win Rate</span>
                </div>
              </div>
            )}

            {/* Rank 1 - Center */}
            {topThree[0] && (
              <div className="bg-gradient-to-b from-slate-900/40 to-orange-950/10 border border-orange-500/30 rounded-3xl p-7 text-center space-y-4 backdrop-blur-md order-1 sm:order-2 sm:h-[260px] flex flex-col justify-end relative overflow-hidden shadow-xl shadow-orange-500/5">
                <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500" />
                <div className="absolute top-4 right-4 flex items-center justify-center size-7 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400">
                  <Star className="size-4 fill-current animate-pulse" />
                </div>
                <div className="relative size-20 mx-auto rounded-full overflow-hidden border-2 border-yellow-500 shadow-xl shadow-yellow-500/20">
                  <img 
                    src={topThree[0].avatarUrl || `https://cdn.discordapp.com/embed/avatars/${(parseInt(topThree[0].id) || 0) % 5}.png`} 
                    alt={topThree[0].username}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${topThree[0].username}`;
                    }}
                  />
                </div>
                <div>
                  <h3 className="font-extrabold text-white text-lg truncate">{topThree[0].username}</h3>
                  <p className="text-xs text-yellow-500 font-bold uppercase tracking-widest mt-1 flex items-center justify-center gap-1">
                    <Trophy className="size-3.5" />
                    Champion
                  </p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-300 border-t border-slate-800/60 pt-3">
                  <span className="font-bold text-orange-400 font-mono text-sm">{topThree[0].elo} ELO</span>
                  <span className="font-bold text-slate-200">{topThree[0].winRate}% Win Rate</span>
                </div>
              </div>
            )}

            {/* Rank 3 - Right */}
            {topThree[2] && (
              <div className="bg-slate-900/30 border border-slate-850/60 rounded-2xl p-6 text-center space-y-4 backdrop-blur-md order-3 sm:order-3 sm:h-[210px] flex flex-col justify-end relative overflow-hidden">
                <div className="absolute top-0 inset-x-0 h-1 bg-amber-700" />
                <div className="relative size-14 mx-auto rounded-full overflow-hidden border-2 border-amber-700 shadow-lg shadow-amber-700/10">
                  <img 
                    src={topThree[2].avatarUrl || `https://cdn.discordapp.com/embed/avatars/${(parseInt(topThree[2].id) || 0) % 5}.png`} 
                    alt={topThree[2].username}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${topThree[2].username}`;
                    }}
                  />
                </div>
                <div>
                  <h3 className="font-bold text-slate-200 truncate">{topThree[2].username}</h3>
                  <p className="text-xs text-slate-500 font-semibold uppercase tracking-widest mt-1">3rd Place</p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-900 pt-3">
                  <span className="font-mono">{topThree[2].elo} ELO</span>
                  <span className="font-semibold text-slate-300">{topThree[2].winRate}% Win Rate</span>
                </div>
              </div>
            )}

          </div>
        )}

        {/* Leaderboard Table for other players */}
        <div className="bg-slate-900/20 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-md">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/80 bg-slate-950/40 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                <th className="py-4 px-6 text-center w-20">Rank</th>
                <th className="py-4 px-6">Trainer</th>
                <th className="py-4 px-6 text-center">ELO Rating</th>
                <th className="py-4 px-6 text-center">Win Rate</th>
                <th className="py-4 px-6 text-center">W / L Record</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900/60 text-sm">
              {restOfList.map((user) => (
                <tr key={user.username} className="hover:bg-slate-900/10 transition">
                  <td className="py-4 px-6 text-center font-bold text-slate-400">
                    {user.rank}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="size-8 rounded-full overflow-hidden border border-slate-800 shrink-0">
                        <img 
                          src={user.avatarUrl || `https://cdn.discordapp.com/embed/avatars/${(parseInt(user.id) || 0) % 5}.png`} 
                          alt="" 
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`;
                          }}
                        />
                      </div>
                      <span className="font-semibold text-slate-200">{user.username}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-center font-bold font-mono text-orange-400/90">
                    {user.elo}
                  </td>
                  <td className="py-4 px-6 text-center font-semibold text-slate-300">
                    {user.winRate}%
                  </td>
                  <td className="py-4 px-6 text-center text-slate-400 font-medium">
                    <span className="text-green-500 font-semibold">{user.wins}</span>
                    {" - "}
                    <span className="text-red-500 font-semibold">{user.losses}</span>
                  </td>
                </tr>
              ))}
              
              {leaderboard.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-slate-500 font-semibold">
                    No placement records found. Complete a PvP match to enter the leaderboard!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}

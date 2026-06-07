import React, { useEffect, useState } from 'react';
import { apiFetch } from '@/api/client';
import { Swords, Calendar, Clock, RotateCcw, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { 
  Empty, 
  EmptyHeader, 
  EmptyTitle, 
  EmptyDescription, 
  EmptyMedia 
} from '@/components/ui/empty';

interface BattleRecord {
  id: string;
  opponent: string;
  opponentAvatar: string;
  result: 'win' | 'loss';
  myTeam: string;
  opponentTeam: string;
  eloChange: number;
  timestamp: string;
  duration: string;
  turns: number;
}

interface BattleHistoryResponse {
  battles: BattleRecord[];
  updatedAt: string;
}

export default function BattleHistoryPage() {
  const [battles, setBattles] = useState<BattleRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadBattles = () => {
    setLoading(true);
    apiFetch<BattleHistoryResponse>('/api/battles/history')
      .then((res) => {
        setBattles(res.battles || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load battle history');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadBattles();
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
          onClick={loadBattles}
          className="bg-slate-800 text-slate-200 border border-slate-700 px-4 py-2 rounded-xl text-xs font-bold"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="w-full text-slate-100 min-h-screen pb-12">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/20 p-5 rounded-2xl border border-slate-800/60 backdrop-blur-md">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
              <Swords className="size-6 text-red-500" />
              Combat Log
            </h1>
            <p className="text-slate-400 text-xs mt-0.5">
              Review your recent battles, outcomes, and ELO adjustments.
            </p>
          </div>
          <button
            onClick={loadBattles}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs px-4 py-2.5 rounded-xl transition border border-slate-700 shrink-0"
          >
            <RefreshCw className="size-3.5" />
            Refresh Logs
          </button>
        </div>

        {/* List of Battles */}
        {battles.length > 0 ? (
          <div className="space-y-4">
            {battles.map((battle) => {
              const isWin = battle.result === 'win';
              return (
                <div 
                  key={battle.id}
                  className={`border rounded-2xl p-5 backdrop-blur-md transition duration-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/20 ${
                    isWin 
                      ? 'border-green-500/20 hover:border-green-500/40 shadow-lg shadow-green-500/2'
                      : 'border-red-500/20 hover:border-red-500/40 shadow-lg shadow-red-500/2'
                  }`}
                >
                  
                  {/* Left: Outcome and Opponent info */}
                  <div className="flex items-center gap-4">
                    {/* Outcome Tag */}
                    <div className={`w-16 text-center font-extrabold text-xs tracking-wider uppercase px-2.5 py-1.5 rounded-lg border shrink-0 ${
                      isWin 
                        ? 'bg-green-500/10 border-green-500/20 text-green-400'
                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                    }`}>
                      {battle.result}
                    </div>

                    {/* Opponent Profile */}
                    <div className="flex items-center gap-3">
                      <div className="size-9 rounded-full overflow-hidden border border-slate-800 shrink-0 bg-slate-900">
                        <img 
                          src={battle.opponentAvatar} 
                          alt="" 
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${battle.opponent}`;
                          }}
                        />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-200">vs {battle.opponent}</span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-semibold uppercase mt-0.5 tracking-wider">
                          Squad: <span className="text-slate-400">{battle.opponentTeam || 'Default'}</span>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Center: Match Details (Turns, duration, time elapsed) */}
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-400 font-medium">
                    <div className="flex items-center gap-1.5">
                      <RotateCcw className="size-3.5 text-slate-500" />
                      <span>{battle.turns} Turns</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="size-3.5 text-slate-500" />
                      <span>{battle.duration} Min</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="size-3.5 text-slate-500" />
                      <span>{battle.timestamp}</span>
                    </div>
                  </div>

                  {/* Right: ELO Adjustment */}
                  <div className="shrink-0 flex items-center gap-2 justify-end w-full sm:w-auto border-t sm:border-t-0 border-slate-900 pt-3 sm:pt-0">
                    <span className="text-xs text-slate-500 font-semibold uppercase">Elo Change</span>
                    <div className={`flex items-center gap-1 font-bold font-mono text-sm px-2.5 py-1 rounded-lg border ${
                      battle.eloChange >= 0
                        ? 'bg-green-500/10 border-green-500/20 text-green-400'
                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                    }`}>
                      {battle.eloChange >= 0 ? (
                        <>
                          <TrendingUp className="size-3.5" />
                          <span>+{battle.eloChange}</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="size-3.5" />
                          <span>{battle.eloChange}</span>
                        </>
                      )}
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        ) : (
          <Empty className="bg-slate-900/20 border-slate-800/80 rounded-2xl py-16">
            <EmptyMedia variant="icon" className="bg-slate-850 text-red-400 size-12 border border-slate-750">
              <Swords className="size-6" />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle className="text-slate-200 text-xl font-bold font-sans">No Combat Records</EmptyTitle>
              <EmptyDescription className="text-slate-400 mt-2">
                You haven't fought any battles yet. Invite someone in your Discord servers to battle by typing `/battle @user`!
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}

      </div>
    </div>
  );
}

import React from "react";
import { motion } from "framer-motion";

export const Hero = ({ onLogin, onShowTips, showTips }: { onLogin: () => void, onShowTips: () => void, showTips: boolean }) => {
  return (
    <div className="relative isolate overflow-hidden bg-bg-primary">
      {/* Background gradients */}
      <div
        aria-hidden="true"
        className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
      >
        <div
          style={{
            clipPath:
              'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
          }}
          className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
        />
      </div>

      <div className="mx-auto max-w-7xl px-6 pb-24 pt-10 sm:pb-32 lg:flex lg:px-8 lg:py-40">
        <div className="mx-auto max-w-2xl flex-shrink-0 lg:mx-0 lg:max-w-xl lg:pt-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-24 sm:mt-32 lg:mt-16"
          >
            <a href="https://github.com/Jules-Agent/pokemonduel/releases" target="_blank" rel="noreferrer" className="inline-flex space-x-6">
              <span className="rounded-full bg-accent/10 px-3 py-1 text-sm font-semibold leading-6 text-accent ring-1 ring-inset ring-accent/20">
                Latest updates
              </span>
              <span className="inline-flex items-center space-x-2 text-sm font-medium leading-6 text-text-secondary">
                <span>Just shipped v1.0</span>
                <span className="text-text-muted" aria-hidden="true">&rarr;</span>
              </span>
            </a>
          </motion.div>
          <motion.h1
             initial={{ opacity: 0, y: 20 }}
             animate={{ opacity: 1, y: 0 }}
             transition={{ duration: 0.5, delay: 0.1 }}
             className="mt-10 font-display text-4xl font-bold tracking-tight text-white sm:text-6xl"
          >
            Master Your Pokémon <span className="text-accent">Strategy</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-lg leading-8 text-text-secondary"
          >
            Build, manage, and optimize your teams for competitive battles. Connect your Discord account to sync directly with your bot's database and dominate the arena.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-10 flex items-center gap-x-6"
          >
            <button
              onClick={onLogin}
              className="rounded-xl bg-accent px-8 py-4 text-sm font-semibold text-bg-primary shadow-sm hover:bg-accent-soft hover:shadow-[0_0_20px_rgba(207,162,64,0.3)] transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              Connect with Discord
            </button>
            <a href="https://github.com/Jules-Agent/pokemonduel" target="_blank" rel="noreferrer" className="text-sm font-semibold leading-6 text-white hover:text-accent transition-colors">
              View on GitHub <span aria-hidden="true">→</span>
            </a>
          </motion.div>

          <motion.div
             initial={{ opacity: 0, y: 20 }}
             animate={{ opacity: 1, y: 0 }}
             transition={{ duration: 0.5, delay: 0.4 }}
             className="mt-8"
          >
            <button
              onClick={onShowTips}
              className="text-xs text-text-muted hover:text-text-secondary underline transition-colors"
            >
              Having trouble logging in?
            </button>
            {showTips && (
               <motion.div
                 initial={{ opacity: 0, height: 0 }}
                 animate={{ opacity: 1, height: 'auto' }}
                 className="mt-4 text-xs text-left text-amber-500 bg-amber-500/5 border border-amber-500/20 p-4 rounded-xl leading-relaxed"
               >
                 <p className="font-semibold mb-2">Configuration Checklist:</p>
                 <ul className="list-disc pl-5 space-y-1">
                   <li>Verify Client ID in <code>.env</code> matches your Discord application.</li>
                   <li>Add <code>http://localhost:3001/api/auth/callback</code> to your Redirect URIs in the Discord Developer Portal.</li>
                   <li>Ensure the bot is running on the correct port.</li>
                 </ul>
               </motion.div>
            )}
          </motion.div>
        </div>

        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ duration: 0.7, delay: 0.3 }}
           className="mx-auto mt-16 flex max-w-2xl sm:mt-24 lg:ml-10 lg:mr-0 lg:mt-0 lg:max-w-none lg:flex-none xl:ml-32"
        >
          <div className="max-w-3xl flex-none sm:max-w-5xl lg:max-w-none">
            <div className="rounded-2xl bg-bg-card/40 p-2 ring-1 ring-white/10 lg:rounded-3xl lg:p-4 backdrop-blur-sm">
              <div className="relative rounded-xl border border-white/10 bg-bg-secondary/80 shadow-2xl p-8 overflow-hidden h-[500px] w-[600px] flex flex-col items-center justify-center group">
                 {/* Decorative elements representing the app UI */}
                 <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent to-emerald-500"></div>

                 <div className="grid grid-cols-2 gap-4 w-full opacity-80 group-hover:opacity-100 transition-opacity">
                    {[1,2,3,4].map(i => (
                        <div key={i} className="bg-bg-card border border-white/5 rounded-xl p-4 flex gap-4 items-center">
                            <div className="w-12 h-12 rounded-full bg-white/5 animate-pulse"></div>
                            <div className="space-y-2 flex-1">
                                <div className="h-4 w-24 bg-white/10 rounded"></div>
                                <div className="h-3 w-16 bg-white/5 rounded"></div>
                            </div>
                        </div>
                    ))}
                 </div>

                 <div className="absolute inset-0 bg-gradient-to-t from-bg-secondary via-transparent to-transparent"></div>

                 <div className="absolute bottom-10 px-8 text-center">
                    <div className="inline-flex gap-4 mb-4">
                        <div className="bg-bg-card/80 backdrop-blur border border-white/10 px-4 py-2 rounded-lg text-sm text-emerald-400 font-mono">
                            Syncing: Active
                        </div>
                        <div className="bg-bg-card/80 backdrop-blur border border-white/10 px-4 py-2 rounded-lg text-sm text-accent font-mono">
                            ELO: 1540
                        </div>
                    </div>
                 </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Feature section */}
      <div className="mx-auto max-w-7xl px-6 pb-24 sm:pb-32 lg:px-8">
        <div className="mx-auto max-w-2xl lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {[
              {
                name: 'Real-time Synchronization',
                description: 'Changes made to your teams are instantly synced with your Discord bot database. No more manual updates.',
                icon: '🔄'
              },
              {
                name: 'Advanced Team Builder',
                description: 'Fine-tune EVs, IVs, Natures, and Movesets with an intuitive, spreadsheet-like interface built for power users.',
                icon: '⚔️'
              },
              {
                name: 'Comprehensive Database',
                description: 'Access complete data for over 1.4k Pokémon forms, items, abilities, and moves, directly within the editor.',
                icon: '📚'
              }
            ].map((feature, i) => (
              <motion.div
                key={feature.name}
                className="flex flex-col"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 + (i * 0.1) }}
              >
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 ring-1 ring-white/10 text-xl">
                    {feature.icon}
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-text-secondary">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
};

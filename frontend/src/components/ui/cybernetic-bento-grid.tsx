import React, { useEffect, useRef } from 'react';

// Reusable BentoItem component
const BentoItem = ({ className = "", children }: { className?: string; children: React.ReactNode }) => {
    const itemRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const item = itemRef.current;
        if (!item) return;

        const handleMouseMove = (e: MouseEvent) => {
            const rect = item.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            item.style.setProperty('--mouse-x', `${x}px`);
            item.style.setProperty('--mouse-y', `${y}px`);
        };

        item.addEventListener('mousemove', handleMouseMove);

        return () => {
            item.removeEventListener('mousemove', handleMouseMove);
        };
    }, []);

    return (
        <div ref={itemRef} className={`bento-item border border-[var(--border-default)] bg-[var(--bg-raised)] rounded-xl p-6 relative overflow-hidden transition-all duration-300 hover:border-[var(--border-bright)] ${className}`}>
            <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                 style={{
                   background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(0, 176, 255, 0.06), transparent 80%)"
                 }}
            />
            {children}
        </div>
    );
};

// Main Component
export const CyberneticBentoGrid = () => {
    return (
        <div className="w-full z-10">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-text-primary text-center mb-8 font-display uppercase tracking-wider">
              Core Battle Systems
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <BentoItem className="md:col-span-2 md:row-span-2 flex flex-col justify-between min-h-[300px]">
                    <div>
                        <h3 className="text-xl font-bold text-text-primary uppercase font-rajdhani tracking-wider">
                          Real-time Stats Analytics
                        </h3>
                        <p className="mt-2 text-text-secondary text-xs font-sans leading-relaxed">
                          Monitor your trainer rank, wins, losses, and battle ratio performance with live data relays directly synced to Silph Co. databases.
                        </p>
                    </div>
                    <div className="mt-4 h-40 bg-[var(--bg-input)] border border-[var(--border-subtle)] rounded-lg flex flex-col items-center justify-center text-text-muted font-mono text-[10px] uppercase gap-2">
                        <div className="w-6 h-6 border border-dashed border-text-muted rounded-full animate-spin-pokeball" />
                        <span>Aggregating Battle logs...</span>
                    </div>
                </BentoItem>
                <BentoItem>
                    <h3 className="text-lg font-bold text-text-primary uppercase font-rajdhani tracking-wider">
                      Global Matchmaking
                    </h3>
                    <p className="mt-2 text-text-secondary text-xs leading-relaxed font-sans">
                      Instantly connect and challenge trainers worldwide inside the Discord Arena or live web portal.
                    </p>
                </BentoItem>
                <BentoItem>
                    <h3 className="text-lg font-bold text-text-primary uppercase font-rajdhani tracking-wider">
                      Secure Auth Link
                    </h3>
                    <p className="mt-2 text-text-secondary text-xs leading-relaxed font-sans">
                      Discord OAuth linkage ensures your squad state, settings, and stats history remain verified.
                    </p>
                </BentoItem>
                <BentoItem className="md:row-span-2 flex flex-col justify-between">
                    <div>
                        <h3 className="text-lg font-bold text-text-primary uppercase font-rajdhani tracking-wider">
                          Automated Sync
                        </h3>
                        <p className="mt-2 text-text-secondary text-xs leading-relaxed font-sans">
                          Your teams, item bindings, and move allocations are backed up automatically to our cloud servers.
                        </p>
                    </div>
                    <div className="mt-4 h-24 bg-[var(--bg-input)] border border-[var(--border-subtle)] rounded-lg flex items-center justify-center text-text-muted font-mono text-[9px] uppercase">
                      Sync Status: OK
                    </div>
                </BentoItem>
                <BentoItem className="md:col-span-2">
                    <h3 className="text-lg font-bold text-text-primary uppercase font-rajdhani tracking-wider">
                      Serverless Battle Engine
                    </h3>
                    <p className="mt-2 text-text-secondary text-xs leading-relaxed font-sans">
                      Powered by the Smogon Showdown simulator core for fast turn resolution and precise battle logic execution.
                    </p>
                </BentoItem>
            </div>
        </div>
    );
};

export default CyberneticBentoGrid;

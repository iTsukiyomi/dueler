import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge"
import {
  Blocks,
  ChevronsUpDown,
  FileClock,
  GraduationCap,
  Layout,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  MessagesSquare,
  Plus,
  Settings,
  Trophy,
  UserCircle,
  UserCog,
  UserSearch,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";

const sidebarVariants = {
  open: {
    width: "15rem",
  },
  closed: {
    width: "3.05rem",
  },
};

const contentVariants = {
  open: { display: "block", opacity: 1 },
  closed: { display: "block", opacity: 1 },
};

const variants = {
  open: {
    x: 0,
    opacity: 1,
    transition: {
      x: { stiffness: 1000, velocity: -100 },
    },
  },
  closed: {
    x: -20,
    opacity: 0,
    transition: {
      x: { stiffness: 100 },
    },
  },
};

const transitionProps = {
  type: "tween",
  ease: "easeOut",
  duration: 0.2,
  staggerChildren: 0.1,
};

const staggerVariants = {
  open: {
    transition: { staggerChildren: 0.03, delayChildren: 0.02 },
  },
};

export function SessionNavBar({ 
  wins = 0, 
  losses = 0, 
  winRate = "0.0", 
  username = "Trainer", 
  avatarUrl = "", 
  userId = "",
  onSignOut 
}: { 
  wins?: number; 
  losses?: number; 
  winRate?: string; 
  username?: string; 
  avatarUrl?: string; 
  userId?: string;
  onSignOut?: () => void;
}) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const location = useLocation();
  const pathname = location.pathname;

  return (
    <motion.div
      className={cn(
        "sidebar fixed left-0 z-40 h-full shrink-0 border-r border-[var(--border-default)]",
      )}
      initial={isCollapsed ? "closed" : "open"}
      animate={isCollapsed ? "closed" : "open"}
      variants={sidebarVariants}
      transition={transitionProps}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      <motion.div
        className={`relative z-40 flex text-muted-foreground h-full shrink-0 flex-col bg-[var(--bg-base)] transition-all`}
        variants={contentVariants}
      >
        <motion.ul variants={staggerVariants} className="flex h-full flex-col list-none p-0 m-0">
          <div className="flex grow flex-col items-center">
            {/* Top Brand / Org selector */}
            <div className="flex h-[54px] w-full shrink-0 border-b border-[var(--border-default)] p-2">
              <div className="mt-[1.5px] flex w-full">
                <DropdownMenu modal={false}>
                  <DropdownMenuTrigger className="w-full" asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex w-fit items-center gap-2 px-2 text-text-primary hover:bg-[var(--bg-raised)] cursor-pointer" 
                    >
                      <Avatar className="rounded size-4 bg-[var(--bg-raised)] border border-[var(--border-default)]">
                        <AvatarFallback className="text-[8px]">FD</AvatarFallback>
                      </Avatar>
                      <motion.li
                        variants={variants}
                        className="flex w-fit items-center gap-2 list-none"
                      >
                        {!isCollapsed && (
                          <>
                            <p className="text-xs font-bold uppercase tracking-wider font-display text-text-primary">
                              Flame Dueler
                            </p>
                            <ChevronsUpDown className="h-3 w-3 text-text-muted" />
                          </>
                        )}
                      </motion.li>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="bg-[var(--bg-float)] border-[var(--border-bright)] text-text-primary">
                    <DropdownMenuItem asChild className="hover:bg-[var(--bg-raised)] cursor-pointer">
                      <Link to="/dashboard/settings" className="flex items-center gap-2 text-xs font-semibold">
                        <UserCog className="h-4 w-4" /> Manage Profile
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild className="hover:bg-[var(--bg-raised)] cursor-pointer">
                      <Link to="/dashboard/teams" className="flex items-center gap-2 text-xs font-semibold">
                        <Blocks className="h-4 w-4" /> Squad Builder
                      </Link>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            {/* Navigation links */}
            <div className="flex h-full w-full flex-col">
              <div className="flex grow flex-col gap-4">
                <ScrollArea className="h-16 grow p-2">
                  <div className={cn("flex w-full flex-col gap-1")}>
                    <Link
                      to="/dashboard"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition text-text-secondary hover:bg-[var(--bg-raised)] hover:text-text-primary",
                        pathname === "/dashboard" && "bg-[var(--bg-raised)] text-[var(--poke-blue)]",
                      )}
                    >
                      <LayoutDashboard className="h-4 w-4 shrink-0" />
                      <motion.li variants={variants} className="list-none">
                        {!isCollapsed && (
                          <p className="ml-2 text-xs font-bold uppercase tracking-wider font-rajdhani">Trainer Card</p>
                        )}
                      </motion.li>
                    </Link>

                    <Link
                      to="/dashboard/teams"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition text-text-secondary hover:bg-[var(--bg-raised)] hover:text-text-primary",
                        pathname?.includes("teams") && "bg-[var(--bg-raised)] text-[var(--poke-blue)]",
                      )}
                    >
                      <Blocks className="h-4 w-4 shrink-0" />
                      <motion.li variants={variants} className="list-none">
                        {!isCollapsed && (
                          <p className="ml-2 text-xs font-bold uppercase tracking-wider font-rajdhani">Squad Editor</p>
                        )}
                      </motion.li>
                    </Link>

                    <Link
                      to="/dashboard/leaderboard"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition text-text-secondary hover:bg-[var(--bg-raised)] hover:text-text-primary",
                        pathname?.includes("leaderboard") && "bg-[var(--bg-raised)] text-[var(--poke-blue)]",
                      )}
                    >
                      <Trophy className="h-4 w-4 shrink-0" />
                      <motion.li variants={variants} className="list-none">
                        {!isCollapsed && (
                          <p className="ml-2 text-xs font-bold uppercase tracking-wider font-rajdhani">Hall of Fame</p>
                        )}
                      </motion.li>
                    </Link>

                    <Link
                      to="/dashboard/battles"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition text-text-secondary hover:bg-[var(--bg-raised)] hover:text-text-primary",
                        pathname?.includes("battles") && "bg-[var(--bg-raised)] text-[var(--poke-blue)]",
                      )}
                    >
                      <FileClock className="h-4 w-4 shrink-0" />
                      <motion.li variants={variants} className="list-none">
                        {!isCollapsed && (
                          <div className="ml-2 flex items-center gap-2">
                            <p className="text-xs font-bold uppercase tracking-wider font-rajdhani">Battle Logs</p>
                          </div>
                        )}
                      </motion.li>
                    </Link>

                    <Separator className="w-full bg-[var(--border-default)] my-1" />

                    <Link
                      to="/dashboard/settings"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition text-text-secondary hover:bg-[var(--bg-raised)] hover:text-text-primary",
                        pathname?.includes("settings") && "bg-[var(--bg-raised)] text-[var(--poke-blue)]",
                      )}
                    >
                      <Settings className="h-4 w-4 shrink-0" />
                      <motion.li variants={variants} className="list-none">
                        {!isCollapsed && (
                          <p className="ml-2 text-xs font-bold uppercase tracking-wider font-rajdhani">OS Settings</p>
                        )}
                      </motion.li>
                    </Link>
                  </div>
                </ScrollArea>
              </div>

              {/* Record Summary when Expanded */}
              {!isCollapsed && (
                <div className="px-4 py-2 border-t border-[var(--border-default)] bg-[var(--bg-raised)] mx-2 rounded-lg mb-2">
                  <div className="text-[8px] font-mono text-text-muted uppercase tracking-widest mb-1.5">League Record</div>
                  <div className="grid grid-cols-3 gap-1 text-[10px] font-mono font-bold text-center">
                    <div>
                      <div className="text-text-secondary">W</div>
                      <div className="text-emerald-400 mt-0.5">{wins}</div>
                    </div>
                    <div>
                      <div className="text-text-secondary">L</div>
                      <div className="text-[var(--poke-red)] mt-0.5">{losses}</div>
                    </div>
                    <div>
                      <div className="text-text-secondary">%</div>
                      <div className="text-[var(--poke-yellow)] mt-0.5">{winRate}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Footer Account Actions */}
              <div className="flex flex-col p-2 border-t border-[var(--border-default)]">
                <div>
                  <DropdownMenu modal={false}>
                    <DropdownMenuTrigger className="w-full outline-none">
                      <div className="flex h-8 w-full flex-row items-center gap-2 rounded-md px-2 py-1.5 transition hover:bg-[var(--bg-raised)] hover:text-text-primary cursor-pointer text-text-secondary">
                        <Avatar className="size-4 bg-[var(--bg-raised)] border border-[var(--border-default)]">
                          {avatarUrl ? (
                            <img src={avatarUrl} alt={username} className="object-cover size-full rounded-full" />
                          ) : (
                            <AvatarFallback className="text-[8px]">{username.slice(0,2).toUpperCase()}</AvatarFallback>
                          )}
                        </Avatar>
                        <motion.li
                          variants={variants}
                          className="flex w-full items-center gap-2 list-none"
                        >
                          {!isCollapsed && (
                            <>
                              <p className="text-xs font-semibold uppercase font-rajdhani tracking-wider truncate text-left max-w-[80px]">{username}</p>
                              <ChevronsUpDown className="ml-auto h-3 w-3 text-text-muted" />
                            </>
                          )}
                        </motion.li>
                      </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent sideOffset={5} className="bg-[var(--bg-float)] border-[var(--border-bright)] text-text-primary">
                      <div className="flex flex-row items-center gap-2 p-2 min-w-[150px]">
                        <Avatar className="size-6 bg-[var(--bg-raised)] border border-[var(--border-default)]">
                          {avatarUrl ? (
                            <img src={avatarUrl} alt={username} className="object-cover size-full rounded-full" />
                          ) : (
                            <AvatarFallback className="text-xs">{username.slice(0,2).toUpperCase()}</AvatarFallback>
                          )}
                        </Avatar>
                        <div className="flex flex-col text-left">
                          <span className="text-xs font-bold uppercase font-rajdhani tracking-wider text-text-primary">
                            {username}
                          </span>
                          {userId && (
                            <span className="text-[8px] font-mono text-text-muted">
                              ID: {userId}
                            </span>
                          )}
                        </div>
                      </div>
                      <DropdownMenuSeparator className="bg-[var(--border-default)]" />
                      <DropdownMenuItem asChild className="hover:bg-[var(--bg-raised)] cursor-pointer">
                        <Link to="/dashboard/settings" className="flex items-center gap-2 text-xs font-semibold">
                          <UserCircle className="h-4 w-4" /> Profile
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={onSignOut} className="flex items-center gap-2 text-xs font-semibold hover:bg-[var(--bg-raised)] text-[var(--poke-red)] cursor-pointer">
                        <LogOut className="h-4 w-4" /> Sign out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          </div>
        </motion.ul>
      </motion.div>
    </motion.div>
  );
}

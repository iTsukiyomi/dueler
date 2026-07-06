import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge"
import {
  ChevronsUpDown,
  LayoutDashboard,
  LogOut,
  MessagesSquare,
  Swords,
  Trophy,
  Users,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
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
import { useAuthStore } from "@/stores/authStore";

const sidebarVariants = {
  open: {
    width: "16rem",
  },
  closed: {
    width: "3.75rem",
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
  type: "tween" as const,
  ease: "easeOut",
  duration: 0.2,
  staggerChildren: 0.1,
};

const staggerVariants = {
  open: {
    transition: { staggerChildren: 0.03, delayChildren: 0.02 },
  },
};

export function SessionNavBar() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const { pathname } = useLocation();
  const { user, profile, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
  };

  const navItems = [
    {
      to: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      active: pathname === "/dashboard",
    },
    {
      to: "/dashboard/teams",
      label: "My Squads",
      icon: Users,
      active: pathname.startsWith("/dashboard/teams"),
    },
    {
      to: "/dashboard/chat",
      label: "Gemini Chat",
      icon: MessagesSquare,
      active: pathname === "/dashboard/chat",
      badge: "AI",
    },
    {
      to: "/dashboard/leaderboard",
      label: "Leaderboard",
      icon: Trophy,
      active: pathname === "/dashboard/leaderboard",
    },
    {
      to: "/dashboard/battles",
      label: "Battle History",
      icon: Swords,
      active: pathname === "/dashboard/battles",
    },
  ];

  return (
    <motion.div
      className={cn(
        "sidebar fixed left-0 top-0 z-40 h-full shrink-0 border-r border-slate-800 bg-slate-950/80 backdrop-blur-md text-white select-none"
      )}
      initial={isCollapsed ? "closed" : "open"}
      animate={isCollapsed ? "closed" : "open"}
      variants={sidebarVariants}
      transition={transitionProps as any}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      <motion.div
        className="relative z-40 flex flex-col h-full shrink-0 bg-slate-950/40"
        variants={contentVariants}
      >
        <motion.ul variants={staggerVariants} className="flex h-full flex-col p-0 m-0 list-none">
          {/* Logo Section */}
          <div className="flex h-[60px] w-full shrink-0 border-b border-slate-800 p-3 items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="size-8 rounded-lg bg-gradient-to-br from-red-500 via-orange-500 to-yellow-500 flex items-center justify-center font-bold text-white shadow-lg shadow-orange-500/20">
                P
              </div>
              {!isCollapsed && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-400 text-sm tracking-wider uppercase font-sans whitespace-nowrap"
                >
                  Darkmew
                </motion.span>
              )}
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex h-full w-full flex-col grow justify-between py-4">
            <ScrollArea className="grow px-2">
              <div className="flex w-full flex-col gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={cn(
                        "flex h-10 w-full flex-row items-center rounded-lg px-3 py-2 transition duration-200 group relative",
                        item.active
                          ? "bg-gradient-to-r from-orange-500/20 to-red-500/10 border-l-2 border-orange-500 text-orange-400"
                          : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                      )}
                    >
                      <Icon className={cn("size-4 shrink-0", item.active ? "text-orange-400" : "text-slate-400 group-hover:text-slate-100")} />
                      
                      {!isCollapsed && (
                        <motion.li variants={variants} className="list-none flex items-center justify-between w-full ml-3">
                          <span className="text-sm font-medium">{item.label}</span>
                          {item.badge && (
                            <Badge className="bg-red-500/20 text-red-400 border-none text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold tracking-wider font-sans">
                              {item.badge}
                            </Badge>
                          )}
                        </motion.li>
                      )}
                    </Link>
                  );
                })}
              </div>
            </ScrollArea>

            {/* Bottom Profile / Account section */}
            <div className="flex flex-col p-2 gap-1 border-t border-slate-900">
              <DropdownMenu modal={false}>
                <DropdownMenuTrigger className="w-full focus:outline-none" asChild>
                  <div className="flex h-12 w-full flex-row items-center gap-2 rounded-lg px-2 py-1.5 transition hover:bg-slate-900 hover:text-slate-100 cursor-pointer text-left">
                    <Avatar className="size-7 border border-slate-700">
                      <AvatarImage src={user?.avatarUrl} alt={user?.username} />
                      <AvatarFallback className="bg-slate-800 text-slate-300 uppercase text-xs font-semibold">
                        {user?.username?.substring(0, 2) || "TR"}
                      </AvatarFallback>
                    </Avatar>
                    
                    {!isCollapsed && (
                      <motion.li
                        variants={variants}
                        className="flex w-full items-center justify-between list-none"
                      >
                        <div className="flex flex-col truncate">
                          <p className="text-sm font-semibold m-0 text-slate-200 truncate">
                            {user?.username || "Trainer"}
                          </p>
                          <p className="text-xs text-orange-500/90 font-medium m-0">
                            {profile?.elo !== undefined ? `${profile.elo} ELO` : "Trainer Hub"}
                          </p>
                        </div>
                        <ChevronsUpDown className="size-3 text-slate-500" />
                      </motion.li>
                    )}
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" side="right" className="bg-slate-950 border-slate-800 text-slate-200 w-52 p-1">
                  <div className="flex flex-row items-center gap-2 p-2">
                    <Avatar className="size-8 border border-slate-800">
                      <AvatarImage src={user?.avatarUrl} alt={user?.username} />
                      <AvatarFallback className="bg-slate-800 text-slate-300 uppercase">
                        {user?.username?.substring(0, 2) || "TR"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col text-left truncate">
                      <span className="text-sm font-semibold text-slate-200 truncate">
                        {user?.username || "Trainer"}
                      </span>
                      <span className="text-xs text-slate-500 truncate">
                        ID: {user?.id}
                      </span>
                    </div>
                  </div>
                  <DropdownMenuSeparator className="bg-slate-800" />
                  <DropdownMenuItem
                    asChild
                    className="flex items-center gap-2 cursor-pointer focus:bg-slate-900 focus:text-slate-100 p-2 rounded-md"
                  >
                    <Link to="/dashboard">
                      <LayoutDashboard className="size-4 text-slate-400" /> Trainer Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="flex items-center gap-2 cursor-pointer focus:bg-red-950/30 focus:text-red-400 p-2 rounded-md text-red-500 font-medium"
                  >
                    <LogOut className="size-4" /> Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </motion.ul>
      </motion.div>
    </motion.div>
  );
}

import React, { useState, useRef, useEffect, useCallback, useTransition } from 'react';
import { sendChatMessage, ChatMessage } from '@/api/chat';
import { useTeamStore, PokemonSlot } from '@/stores/teamStore';
import { useAuthStore } from '@/stores/authStore';
import { cn } from '@/lib/utils';
import { 
  Plus, 
  Trash2, 
  Send, 
  X, 
  Loader2, 
  Sparkles, 
  Command, 
  Paperclip, 
  Bot, 
  User, 
  BrainCircuit, 
  Swords,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Search,
  BookOpen,
  ShieldAlert
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface LocalMessage {
  id: string;
  sender: 'user' | 'model';
  text: string;
  timestamp: number;
  suggestedTeam?: {
    name: string;
    pokemon: PokemonSlot[];
  };
}

interface ChatSession {
  id: string;
  title: string;
  messages: LocalMessage[];
  timestamp: number;
}

interface CommandSuggestion {
  icon: React.ReactNode;
  label: string;
  description: string;
  prefix: string;
}

export default function ChatPage() {
  const { createTeam } = useTeamStore();
  const { profile } = useAuthStore();
  const [isPending, startTransition] = useTransition();

  // Local storage chat sessions
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Input states
  const [value, setValue] = useState("");
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState<number>(-1);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [inputFocused, setInputFocused] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const commandPaletteRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Command palette suggestions (themed for Pokemon strategy!)
  const commandSuggestions: CommandSuggestion[] = [
    { 
      icon: <Swords className="w-4 h-4 text-red-400" />, 
      label: "Suggest Team", 
      description: "Generate a competitive Gen 9 team", 
      prefix: "/suggest-team" 
    },
    { 
      icon: <BookOpen className="w-4 h-4 text-blue-400" />, 
      label: "Moveset Tip", 
      description: "Get optimization moveset for a species", 
      prefix: "/moveset" 
    },
    { 
      icon: <ShieldAlert className="w-4 h-4 text-yellow-400" />, 
      label: "Find Counter", 
      description: "Suggest counters for a specific Pokemon", 
      prefix: "/counter" 
    },
    { 
      icon: <BrainCircuit className="w-4 h-4 text-green-400" />, 
      label: "Analyze Active", 
      description: "Review your active party strengths", 
      prefix: "/analyze-team" 
    },
  ];

  // Auto-resize textarea logic
  const adjustHeight = useCallback((reset?: boolean) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    if (reset) {
      textarea.style.height = `60px`;
      return;
    }
    textarea.style.height = `60px`;
    const newHeight = Math.max(60, Math.min(textarea.scrollHeight, 200));
    textarea.style.height = `${newHeight}px`;
  }, []);

  // Mouse move listener for focal glow
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Handle outside click for command palette
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      const commandButton = document.querySelector('[data-command-button]');
      if (commandPaletteRef.current && 
          !commandPaletteRef.current.contains(target) && 
          !commandButton?.contains(target)) {
        setShowCommandPalette(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load chat sessions from localStorage on boot
  useEffect(() => {
    try {
      const saved = localStorage.getItem('dueler_chat_sessions');
      if (saved) {
        const parsed = JSON.parse(saved) as ChatSession[];
        if (parsed.length > 0) {
          setSessions(parsed);
          setActiveSessionId(parsed[0].id);
          return;
        }
      }
    } catch (e) {
      console.error('Failed to load chat history', e);
    }
    // Create first session by default if nothing exists
    const firstId = Date.now().toString();
    const defaultSession: ChatSession = {
      id: firstId,
      title: 'New Strategy Chat',
      timestamp: Date.now(),
      messages: [
        {
          id: 'welcome',
          sender: 'model',
          text: `Hello! I am your AI Poké Dueler Assistant, specialized in Gen 9 (Scarlet & Violet) PvP mechanics. Ask me to build a squad, analyze your active roster, or request counters for any Pokémon. Use slash commands like /suggest-team to start!`,
          timestamp: Date.now()
        }
      ]
    };
    setSessions([defaultSession]);
    setActiveSessionId(firstId);
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, activeSessionId, isTyping]);

  // Save sessions to localStorage whenever they change
  const saveSessions = (updated: ChatSession[]) => {
    setSessions(updated);
    try {
      localStorage.setItem('dueler_chat_sessions', JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to save sessions to storage', e);
    }
  };

  // Active session helper
  const activeSession = sessions.find(s => s.id === activeSessionId);

  // Command palette suggestions triggers
  useEffect(() => {
    if (value.startsWith('/') && !value.includes(' ')) {
      setShowCommandPalette(true);
      const matchingIdx = commandSuggestions.findIndex(cmd => cmd.prefix.startsWith(value));
      setActiveSuggestion(matchingIdx >= 0 ? matchingIdx : 0);
    } else {
      setShowCommandPalette(false);
    }
  }, [value]);

  // Extract json-team block helper
  const extractSuggestedTeam = (text: string) => {
    const regex = /```json-team\s*([\s\S]*?)```/;
    const match = text.match(regex);
    
    // Normalization helper for identifiers (lowercase, hyphenated, alphanumeric)
    const formatIdentifier = (str: string): string => {
      if (!str) return '';
      return str
        .trim()
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '')
        .replace(/(^-|-$)/g, '');
    };

    // Normalization helper for natures (Word-Capitalized)
    const formatNature = (str: string): string => {
      if (!str) return 'Hardy';
      const clean = str.trim().toLowerCase();
      if (clean.length === 0) return 'Hardy';
      return clean.charAt(0).toUpperCase() + clean.slice(1);
    };

    if (match && match[1]) {
      try {
        const teamObj = JSON.parse(match[1].trim());
        if (teamObj.name && Array.isArray(teamObj.pokemon)) {
          const normalizedPokemon = teamObj.pokemon.map((p: any, idx: number) => {
            // 1. Sanitize names, moves, item, nature
            const pokname = formatIdentifier(p.pokname || p.name || '');
            const poknick = p.poknick || p.nickname || 'None';
            const hitem = formatIdentifier(p.hitem || p.item || '');
            const nature = formatNature(p.nature || 'Hardy');

            // Sanitize moves array (must be exactly 4 moves)
            let rawMoves = Array.isArray(p.moves) ? p.moves : [];
            const moves = ['', '', '', ''].map((_, mIdx) => {
              const move = rawMoves[mIdx];
              return move ? formatIdentifier(move) : '';
            });

            // 2. Sanitize and clamp IVs (0 - 31)
            const hpiv = Math.max(0, Math.min(31, p.hpiv !== undefined ? Number(p.hpiv) : 31));
            const atkiv = Math.max(0, Math.min(31, p.atkiv !== undefined ? Number(p.atkiv) : 31));
            const defiv = Math.max(0, Math.min(31, p.defiv !== undefined ? Number(p.defiv) : 31));
            const spatkiv = Math.max(0, Math.min(31, p.spatkiv !== undefined ? Number(p.spatkiv) : 31));
            const spdefiv = Math.max(0, Math.min(31, p.spdefiv !== undefined ? Number(p.spdefiv) : 31));
            const speediv = Math.max(0, Math.min(31, p.speediv !== undefined ? Number(p.speediv) : 31));

            // 3. Sanitize and clamp EVs (0 - 252)
            let hpev = Math.max(0, Math.min(252, Math.round(Number(p.hpev) || 0)));
            let atkev = Math.max(0, Math.min(252, Math.round(Number(p.atkev) || 0)));
            let defev = Math.max(0, Math.min(252, Math.round(Number(p.defev) || 0)));
            let spatkev = Math.max(0, Math.min(252, Math.round(Number(p.spatkev) || 0)));
            let spdefev = Math.max(0, Math.min(252, Math.round(Number(p.spdefev) || 0)));
            let speedev = Math.max(0, Math.min(252, Math.round(Number(p.speedev) || 0)));

            // Enforce max EV total of 510
            const evTotal = hpev + atkev + defev + spatkev + spdefev + speedev;
            if (evTotal > 510) {
              const scale = 510 / evTotal;
              hpev = Math.floor(hpev * scale);
              atkev = Math.floor(atkev * scale);
              defev = Math.floor(defev * scale);
              spatkev = Math.floor(spatkev * scale);
              spdefev = Math.floor(spdefev * scale);
              speedev = Math.floor(speedev * scale);

              // Correct any rounding discrepancies
              const newTotal = hpev + atkev + defev + spatkev + spdefev + speedev;
              if (newTotal > 510) {
                hpev = Math.max(0, hpev - (newTotal - 510));
              }
            }

            // 4. Sanitize other fields
            const ability_index = typeof p.ability_index === 'number' && p.ability_index >= 0 && p.ability_index <= 2 
              ? p.ability_index 
              : 0;

            const genderVal = (p.gender || 'M').trim().toUpperCase();
            const gender = genderVal.startsWith('F') ? 'F' : genderVal.startsWith('N') ? 'N' : 'M';

            return {
              id: idx + 1,
              pokname,
              poknick,
              hpiv, atkiv, defiv, spatkiv, spdefiv, speediv,
              hpev, atkev, defev, spatkev, spdefev, speedev,
              moves,
              hitem,
              nature,
              pokelevel: p.pokelevel || 100,
              happiness: p.happiness !== undefined ? p.happiness : 255,
              ability_index,
              gender,
              shiny: !!p.shiny,
              radiant: !!p.radiant,
              skin: p.skin || null
            };
          });

          return {
            name: teamObj.name,
            pokemon: normalizedPokemon,
          };
        }
      } catch (e) {
        console.error('Failed to parse suggested team JSON', e);
      }
    }
    return undefined;
  };

  const cleanMessageText = (text: string) => {
    return text.replace(/```json-team[\s\S]*?```/g, '').trim();
  };

  // Start a new chat session
  const handleNewChat = () => {
    const newId = Date.now().toString();
    const newSess: ChatSession = {
      id: newId,
      title: 'New Strategy Chat',
      timestamp: Date.now(),
      messages: [
        {
          id: 'welcome',
          sender: 'model',
          text: `Hello! I am your AI Poké Dueler Assistant, specialized in Gen 9 (Scarlet & Violet) PvP mechanics. Ask me to build a squad, analyze your active roster, or request counters for any Pokémon. Use slash commands like /suggest-team to start!`,
          timestamp: Date.now()
        }
      ]
    };
    saveSessions([newSess, ...sessions]);
    setActiveSessionId(newId);
    setValue('');
    adjustHeight(true);
  };

  // Delete a chat session
  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const filtered = sessions.filter(s => s.id !== id);
    if (filtered.length === 0) {
      const freshId = Date.now().toString();
      const fresh: ChatSession = {
        id: freshId,
        title: 'New Strategy Chat',
        timestamp: Date.now(),
        messages: [
          {
            id: 'welcome',
            sender: 'model',
            text: `Hello! I am your AI Poké Dueler Assistant, specialized in Gen 9 (Scarlet & Violet) PvP mechanics. Ask me to build a squad, analyze your active roster, or request counters for any Pokémon. Use slash commands like /suggest-team to start!`,
            timestamp: Date.now()
          }
        ]
      };
      saveSessions([fresh]);
      setActiveSessionId(freshId);
    } else {
      saveSessions(filtered);
      if (activeSessionId === id) {
        setActiveSessionId(filtered[0].id);
      }
    }
  };

  // Send message trigger
  const handleSendMessage = async () => {
    if (!value.trim() || isTyping || !activeSession) return;
    
    const userText = value.trim();
    setValue("");
    adjustHeight(true);
    setIsTyping(true);

    const userMessage: LocalMessage = {
      id: Date.now().toString() + '-user',
      sender: 'user',
      text: userText,
      timestamp: Date.now(),
    };

    // Update active session messages
    const updatedMessages = [...activeSession.messages, userMessage];
    
    // Update session title if it was default
    const isDefaultTitle = activeSession.title === 'New Strategy Chat';
    const newTitle = isDefaultTitle 
      ? (userText.length > 25 ? userText.substring(0, 22) + '...' : userText)
      : activeSession.title;

    const updatedSession: ChatSession = {
      ...activeSession,
      title: newTitle,
      messages: updatedMessages,
      timestamp: Date.now()
    };

    const updatedSessionsList = sessions.map(s => s.id === activeSessionId ? updatedSession : s);
    saveSessions(updatedSessionsList);

    try {
      // Map messages history for API (excluding welcome message)
      const apiHistory: ChatMessage[] = updatedMessages
        .filter(m => m.id !== 'welcome')
        .map(m => ({
          role: m.sender === 'user' ? 'user' : 'model',
          parts: [{ text: m.text }]
        }));
      
      // Call endpoint (backend handles fallbacks automatically now)
      const res = await sendChatMessage(userText, apiHistory.slice(0, -1));

      const suggestedTeam = extractSuggestedTeam(res.text);
      const cleaned = cleanMessageText(res.text);

      const botMessage: LocalMessage = {
        id: Date.now().toString() + '-bot',
        sender: 'model',
        text: cleaned || res.text,
        timestamp: Date.now(),
        suggestedTeam
      };

      const finalSession: ChatSession = {
        ...updatedSession,
        messages: [...updatedMessages, botMessage],
        timestamp: Date.now()
      };
      saveSessions(sessions.map(s => s.id === activeSessionId ? finalSession : s));
    } catch (err: any) {
      const errorMsg: LocalMessage = {
        id: Date.now().toString() + '-err',
        sender: 'model',
        text: `Error: Failed to generate chat response: ${err.message || 'Gemini system error'}`,
        timestamp: Date.now(),
      };
      saveSessions(sessions.map(s => s.id === activeSessionId ? { ...updatedSession, messages: [...updatedMessages, errorMsg] } : s));
    } finally {
      setIsTyping(false);
    }
  };

  // Keyboard navigation & controls in text-area
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommandPalette) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveSuggestion(prev => prev < commandSuggestions.length - 1 ? prev + 1 : 0);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveSuggestion(prev => prev > 0 ? prev - 1 : commandSuggestions.length - 1);
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        if (activeSuggestion >= 0) {
          const selected = commandSuggestions[activeSuggestion];
          setValue(selected.prefix + ' ');
          setShowCommandPalette(false);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowCommandPalette(false);
      }
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Select command palette suggestions
  const selectCommandSuggestion = (idx: number) => {
    const selected = commandSuggestions[idx];
    setValue(selected.prefix + ' ');
    setShowCommandPalette(false);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleSaveTeam = async (msgId: string, team: { name: string; pokemon: PokemonSlot[] }) => {
    try {
      await createTeam(team.name, team.pokemon);
      alert(`Roster "${team.name}" imported and saved successfully!`);
      // Update state to remove import widget from current message
      if (activeSession) {
        const updated = activeSession.messages.map(m => m.id === msgId ? { ...m, suggestedTeam: undefined } : m);
        saveSessions(sessions.map(s => s.id === activeSessionId ? { ...activeSession, messages: updated } : s));
      }
    } catch (err: any) {
      alert('Failed to import: ' + err.message);
    }
  };

  const handleAttachFile = () => {
    const mockFile = `trainer-log-${Math.floor(Math.random() * 1000)}.json`;
    setAttachments(prev => [...prev, mockFile]);
  };

  const removeAttachment = (idx: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className="w-full flex h-[calc(100vh-100px)] border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/40 backdrop-blur-md relative shadow-2xl">
      
      {/* GLOW SPOTLIGHT BACKGROUND EFFECT */}
      <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/5 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500/5 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
      </div>

      {/* RECENT CHATS SIDEBAR */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "16rem", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="h-full border-r border-slate-900 bg-slate-950/90 shrink-0 flex flex-col z-10"
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-slate-900 flex justify-between items-center">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recent Chats</span>
              <button 
                onClick={handleNewChat}
                className="size-7 bg-slate-900 hover:bg-slate-800 text-orange-400 border border-slate-800 rounded-lg flex items-center justify-center transition"
                title="New Chat"
              >
                <Plus className="size-4" />
              </button>
            </div>

            {/* Sessions Scroll List */}
            <div className="grow overflow-y-auto p-2 space-y-1">
              {sessions.map((sess) => {
                const isActive = sess.id === activeSessionId;
                return (
                  <div
                    key={sess.id}
                    onClick={() => {
                      setActiveSessionId(sess.id);
                      setValue('');
                      adjustHeight(true);
                    }}
                    className={cn(
                      "flex items-center justify-between p-3 rounded-xl cursor-pointer group transition duration-200",
                      isActive
                        ? "bg-gradient-to-r from-orange-500/20 to-red-500/10 border border-orange-500/30 text-orange-400 font-semibold"
                        : "text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent"
                    )}
                  >
                    <div className="flex items-center gap-2 truncate pr-2">
                      <MessageSquare className="size-4 shrink-0 text-slate-500 group-hover:text-orange-400" />
                      <span className="text-xs truncate capitalize">{sess.title}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteSession(sess.id, e)}
                      className="opacity-0 group-hover:opacity-100 hover:text-red-400 transition size-5 flex items-center justify-center rounded"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* MAIN CHAT SCREEN AREA */}
      <div className="grow flex flex-col h-full z-10 relative bg-slate-950/20 min-w-0">
        
        {/* Chat window top bar */}
        <div className="bg-slate-900/30 border-b border-slate-900 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(prev => !prev)}
              className="size-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-200 transition shrink-0"
            >
              {sidebarOpen ? <ChevronLeft className="size-4" /> : <ChevronRight className="size-4" />}
            </button>
            
            <div className="flex items-center gap-2.5">
              <div className="size-8 rounded-lg bg-orange-600/10 border border-orange-500/20 flex items-center justify-center text-orange-400 shrink-0">
                <BrainCircuit className="size-4.5" />
              </div>
              <div className="truncate">
                <h1 className="text-sm font-bold text-slate-200 leading-none truncate">
                  {activeSession?.title || 'New Strategy Chat'}
                </h1>
                <p className="text-[10px] text-slate-500 mt-1 leading-none">Pokémon Expert AI (Upto Gen 9)</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider shrink-0 select-none">
            <Sparkles className="size-3 animate-pulse" />
            AI Expert
          </div>
        </div>

        {/* Message scroll container */}
        <div className="grow overflow-y-auto p-6 space-y-6">
          
          {/* Greeting view (shows when chat session is empty) */}
          {activeSession && activeSession.messages.length <= 1 && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-12 space-y-8 select-none">
              <div className="space-y-3">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400 pb-1">
                    How can I help today?
                  </h1>
                </motion.div>
                <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                  Analyze squad setups, request moveset advice, or query Scarlet & Violet meta counters.
                </p>
              </div>

              {/* Grid of quick command recommendations */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {commandSuggestions.map((suggestion, idx) => (
                  <button
                    key={suggestion.prefix}
                    onClick={() => selectCommandSuggestion(idx)}
                    className="flex flex-col items-start p-3 bg-slate-900/40 hover:bg-slate-900/80 border border-slate-850 hover:border-slate-800 rounded-xl transition text-left space-y-1 relative group"
                  >
                    <div className="flex items-center gap-2">
                      {suggestion.icon}
                      <span className="text-xs font-bold text-slate-200">{suggestion.label}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 leading-normal">{suggestion.description}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat bubbles list */}
          {activeSession && activeSession.messages.length > 1 && (
            <div className="space-y-6">
              {activeSession.messages.map((msg) => (
                <div 
                  key={msg.id}
                  className={`flex items-start gap-3 w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'model' && (
                    <div className="size-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                      <Bot className="size-4.5 text-orange-400" />
                    </div>
                  )}

                  <div className="max-w-[80%] space-y-3">
                    <div 
                      className={`rounded-2xl p-4 text-sm leading-relaxed border ${
                        msg.sender === 'user'
                          ? 'bg-gradient-to-r from-orange-600 to-red-500 border-orange-500 text-white font-medium shadow-md shadow-orange-600/10'
                          : msg.text.startsWith('Error:')
                            ? 'bg-red-950/20 border-red-900/30 text-red-400'
                            : 'bg-slate-900/40 border-slate-850/80 text-slate-300'
                      }`}
                    >
                      {msg.text.split('\n').map((line, idx) => (
                        <p key={idx} className={idx > 0 ? 'mt-2' : ''}>
                          {line}
                        </p>
                      ))}
                    </div>

                    {/* suggestedTeam card preview block */}
                    {msg.suggestedTeam && (
                      <div className="bg-slate-900/60 border border-orange-500/30 rounded-xl p-4 space-y-4">
                        <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                          <div>
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Suggested Squad</span>
                            <h3 className="text-sm font-bold text-slate-200 capitalize mt-0.5">{msg.suggestedTeam.name}</h3>
                          </div>
                          <button
                            onClick={() => handleSaveTeam(msg.id, msg.suggestedTeam!)}
                            className="bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition"
                          >
                            Import Squad
                          </button>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {msg.suggestedTeam.pokemon.map((p, idx) => (
                            <div key={idx} className="bg-slate-950/50 border border-slate-850 p-2 rounded-lg text-center flex flex-col items-center">
                              <img 
                                src={`https://img.pokemondb.net/sprites/home/normal/${p.pokname.toLowerCase()}.png`}
                                alt=""
                                className="size-10 object-contain drop-shadow"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png';
                                }}
                              />
                              <span className="text-[11px] font-semibold text-slate-300 capitalize truncate w-full mt-1">
                                {p.pokname.replace(/-/g, ' ')}
                              </span>
                              <span className="text-[9px] text-slate-500 capitalize truncate w-full">
                                {p.nature} / {p.hitem ? p.hitem.replace(/-/g, ' ') : 'No Item'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="size-8 rounded-lg bg-orange-600 border border-orange-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-orange-600/10">
                      <User className="size-4" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* INPUT CONTAINER ZONE */}
        <div className="p-4 border-t border-slate-900 relative">
          
          {/* Thinking status indicators */}
          {isTyping && (
            <div className="absolute -top-12 left-6 bg-slate-900 border border-slate-850/80 rounded-full px-4.5 py-1.5 shadow-xl flex items-center gap-2 text-xs text-slate-400 select-none animate-bounce">
              <Loader2 className="size-3.5 animate-spin text-orange-400" />
              <span>Formulating tactics...</span>
            </div>
          )}

          {/* COMMAND PALETTE POPUP */}
          <AnimatePresence>
            {showCommandPalette && (
              <motion.div 
                ref={commandPaletteRef}
                className="absolute left-4 right-4 bottom-full mb-2 bg-slate-950 border border-slate-850 rounded-xl z-20 shadow-2xl p-1 overflow-hidden"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                transition={{ duration: 0.15 }}
              >
                <div className="py-1">
                  {commandSuggestions.map((suggestion, index) => (
                    <div
                      key={suggestion.prefix}
                      onClick={() => selectCommandSuggestion(index)}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 text-xs transition cursor-pointer rounded-lg",
                        activeSuggestion === index 
                          ? "bg-slate-900 text-slate-200" 
                          : "text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
                      )}
                    >
                      <div className="shrink-0">
                        {suggestion.icon}
                      </div>
                      <div className="font-semibold">{suggestion.label}</div>
                      <div className="text-[10px] text-slate-500 truncate grow">{suggestion.description}</div>
                      <div className="text-[10px] font-mono text-slate-600 bg-slate-900/60 px-1.5 py-0.5 rounded shrink-0">
                        {suggestion.prefix}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* TEXT INPUT FRAME */}
          <div className="relative border border-slate-850 bg-slate-950/60 rounded-xl overflow-hidden shadow-inner">
            
            {/* Attachment preview list */}
            {attachments.length > 0 && (
              <div className="px-4 pt-3 flex gap-2 flex-wrap">
                {attachments.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 text-[10px] font-bold bg-slate-900 border border-slate-800 py-1 px-2.5 rounded-lg text-slate-300"
                  >
                    <span>{file}</span>
                    <button 
                      onClick={() => removeAttachment(index)}
                      className="text-slate-500 hover:text-slate-300 transition"
                    >
                      <X className="size-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="p-3">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => {
                  setValue(e.target.value);
                  adjustHeight();
                }}
                onKeyDown={handleKeyDown}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                placeholder="Ask strategy hub a question or type '/' for commands..."
                className="w-full bg-transparent border-none outline-none resize-none text-sm text-slate-200 placeholder:text-slate-600 min-h-[60px] max-h-[200px]"
                style={{ overflow: 'hidden' }}
              />
            </div>

            {/* Input Toolbar */}
            <div className="px-3 pb-3 border-t border-slate-900/60 pt-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleAttachFile}
                  className="size-8 hover:bg-slate-900 text-slate-500 hover:text-slate-350 rounded-lg transition flex items-center justify-center border border-transparent hover:border-slate-800"
                  title="Attach Logs"
                >
                  <Paperclip className="size-4" />
                </button>
                <button
                  type="button"
                  data-command-button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowCommandPalette(prev => !prev);
                  }}
                  className={cn(
                    "size-8 hover:bg-slate-900 text-slate-500 hover:text-slate-350 rounded-lg transition flex items-center justify-center border border-transparent hover:border-slate-800",
                    showCommandPalette && "bg-slate-900 text-orange-400 border-slate-850"
                  )}
                  title="Suggestions"
                >
                  <Command className="size-4" />
                </button>
              </div>
              
              <button
                type="button"
                onClick={handleSendMessage}
                disabled={isTyping || !value.trim()}
                className={cn(
                  "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 duration-300",
                  value.trim()
                    ? "bg-gradient-to-r from-orange-600 to-red-500 hover:from-orange-500 hover:to-red-400 text-white shadow-lg shadow-orange-600/10 cursor-pointer"
                    : "bg-slate-900 text-slate-600 cursor-not-allowed border border-slate-850/40"
                )}
              >
                <Send className="size-3.5" />
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* FLOATING HOVER LIGHTING FOLLOW SPOTLIGHT */}
      {inputFocused && (
        <motion.div 
          className="fixed w-[40rem] h-[40rem] rounded-full pointer-events-none z-0 opacity-[0.015] bg-gradient-to-r from-red-500 via-orange-500 to-yellow-500 blur-[96px]"
          animate={{
            x: mousePosition.x - 320,
            y: mousePosition.y - 320,
          }}
          transition={{
            type: "spring",
            damping: 30,
            stiffness: 120,
            mass: 0.6,
          }}
        />
      )}

    </div>
  );
}

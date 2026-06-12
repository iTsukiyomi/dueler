import { FastifyInstance } from "fastify";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { authMiddleware } from "../middleware/auth.js";
import { getDb } from "../db/mongo.js";
import { config } from "../config.js";

export function extractSuggestedTeam(text: string) {
  const regex = /```json-team\s*([\s\S]*?)```/;
  const match = text.match(regex);
  if (match && match[1]) {
    try {
      const teamObj = JSON.parse(match[1].trim());
      if (teamObj.name && Array.isArray(teamObj.pokemon)) {
        return teamObj;
      }
    } catch (e) {
      console.error("[chat] Failed to parse suggested team JSON:", e);
    }
  }
  return undefined;
}

export function cleanMessageText(text: string) {
  return text.replace(/```json-team[\s\S]*?```/g, "").trim();
}

async function generateGeminiResponse(
  userId: string,
  message: string,
  history: any[],
  db: any,
  defaultUsername: string
): Promise<string> {
  if (!config.geminiApiKey) {
    throw new Error("Gemini API key is not configured in .env file. Please define GEMINI_API_KEY.");
  }

  // 1. Retrieve profile data
  const player = await db.collection("players").findOne({ _id: userId as any });
  const username = player?.username || defaultUsername || "Trainer";
  const wins = player?.wins ?? 0;
  const losses = player?.losses ?? 0;
  const elo = player?.elo ?? 1000;
  const activePartyName = player?.active_party_name ?? "None";
  const theme = player?.theme ?? "default";
  const gen = player?.gen ?? 5;

  // 2. Retrieve current teams
  const teams = await db
    .collection("teams")
    .find({ owner_id: userId, name: { $ne: "__active__" } })
    .toArray();

  // Format teams for context
  const formattedTeams = teams.map((t: any) => ({
    name: t.name,
    is_active: t.name === activePartyName,
    pokemon: (t.pokemon ?? []).map((p: any) => ({
      pokname: p.pokname,
      poknick: p.poknick,
      nature: p.nature,
      hitem: p.hitem,
      moves: p.moves,
      hpiv: p.hpiv,
      atkiv: p.atkiv,
      defiv: p.defiv,
      spatkiv: p.spatkiv,
      spdefiv: p.spdefiv,
      speediv: p.speediv,
      hpev: p.hpev,
      atkev: p.atkev,
      defev: p.defev,
      spatkev: p.spatkev,
      spdefev: p.spdefev,
      speedev: p.speedev,
      shiny: p.shiny,
    })),
  }));

  // 2b. Retrieve ELO rank
  const higherCount = await db.collection("players").countDocuments({
    elo: { $gt: elo },
    $or: [{ wins: { $gt: 0 } }, { losses: { $gt: 0 } }],
  });
  const rank = (wins > 0 || losses > 0) ? higherCount + 1 : "Unranked";

  // 2c. Retrieve recent matches (last 5)
  const recentMatchesDocs = await db.collection("matches")
    .find({
      $or: [{ player1_id: userId }, { player2_id: userId }]
    })
    .sort({ timestamp: -1 })
    .limit(5)
    .toArray();

  const recentMatches = recentMatchesDocs.map((match: any) => {
    const isPlayer1 = match.player1_id === userId;
    const opponentName = isPlayer1 ? match.player2_name : match.player1_name;
    const result = match.winner_id === userId ? "Win" : "Loss";
    const eloChange = isPlayer1 ? match.player1_elo_change : match.player2_elo_change;
    return `${result} vs ${opponentName} (${eloChange >= 0 ? `+${eloChange}` : eloChange} ELO)`;
  }).join(", ") || "No matches played yet";

  // 2d. Retrieve top 5 leaderboard standings
  const topPlayersDocs = await db.collection("players")
    .find({
      $or: [{ wins: { $gt: 0 } }, { losses: { $gt: 0 } }],
    })
    .sort({ elo: -1 })
    .limit(5)
    .toArray();

  const topStandings = topPlayersDocs.map((player: any, index: number) => {
    return `#${index + 1}: ${player.username} (ELO: ${player.elo || 1000})`;
  }).join(", ") || "No ranked players yet";

  // 3. Try generating content with fallback models in case of high demand (503/429)
  const modelsToTry = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b"
  ];

  let text = "";
  let success = false;
  let lastError: any = null;

  for (const modelName of modelsToTry) {
    try {
      console.log(`[chat] Attempting generation with model: ${modelName}`);
      const genAI = new GoogleGenerativeAI(config.geminiApiKey);
      const model = genAI.getGenerativeModel({
        model: modelName,
        systemInstruction: `You are an expert Pokémon Battle Assistant for Flame Dueler, with complete and deep knowledge up to Generation 9 (Scarlet & Violet).
You must use the following player context (such as ELO, win/loss record, active squad, saved squads, recent match history, and top leaderboard rivals) to give highly personalized, contextual, and custom-tailored answers:
- Current user: ${username}
- ELO: ${elo}
- Ladder Rank: ${rank}
- Victories: ${wins}
- Defeats: ${losses}
- Current Theme: ${theme}
- Allowed Gen: ${gen}
- Active Squad Name: ${activePartyName}
- Recent Battle History (last 5 matches): [${recentMatches}]
- Top players on the global ladder: [${topStandings}]
- Saved Squads: ${JSON.stringify(formattedTeams)} (Note: 'is_active' indicates their current active squad)

When the user asks questions about their team, rank, or performance, refer to these stats proactively! 
For example:
- If they ask about their team, analyze the squad where is_active is true.
- If they ask how to climb the ladder, compare their ELO to the top players in the global ladder standings.
- If they ask about their recent form, reference their victories/losses and their recent battle history.

IMPORTANT GENERATION RULES:
1. The user's allowed generation is Gen ${gen}. You MUST ONLY suggest Pokémon, moves, abilities, and items that existed in Generation ${gen} or earlier. Do not suggest or include any content from later generations.
2. If they ask you to suggest or design a new team or update one, please provide it in a standard JSON format inside a code block marked with \`\`\`json-team.
Format the recommended team as a valid JSON object matching the following structure:
\`\`\`json-team
{
  "name": "Squad Name",
  "pokemon": [
    {
      "pokname": "Charizard",
      "poknick": "Lizard",
      "nature": "Adamant",
      "hitem": "life-orb",
      "moves": ["flare-blitz", "dragon-claw", "roost", "earthquake"],
      "hpiv": 31, "atkiv": 31, "defiv": 31, "spatkiv": 31, "spdefiv": 31, "speediv": 31,
      "hpev": 0, "atkev": 252, "defev": 0, "spatkev": 0, "spdefev": 4, "speedev": 252,
      "ability_index": 0,
      "shiny": false
    }
  ]
}
\`\`\`
Important rules for team generation:
1. Ensure all field names like 'pokname', 'poknick', 'hitem', 'hpiv', 'atkev', etc. match EXACTLY.
2. Moves and items should be lowercase and hyphen-separated (e.g. 'flare-blitz', 'life-orb').
3. Keep teams to a maximum of 6 Pokémon.
4. When you provide \`\`\`json-team blocks, the client will parse them and let the user save the team directly to MongoDB with a single click!`,
      });

      // Format chat history for Gemini API
      const contents = [];
      if (history && history.length > 0) {
        for (const msg of history) {
          contents.push({
            role: msg.role === "user" ? "user" : "model",
            parts: [{ text: msg.parts[0].text }],
          });
        }
      }
      contents.push({ role: "user", parts: [{ text: message }] });

      const result = await model.generateContent({ contents });
      const response = await result.response;
      text = response.text();
      
      if (text) {
        success = true;
        console.log(`[chat] Generation succeeded with model: ${modelName}`);
        break;
      }
    } catch (err: any) {
      console.warn(`[chat] Model ${modelName} failed:`, err.message || err);
      lastError = err;
    }
  }

  if (!success) {
    throw new Error(lastError?.message || "All fallback Gemini models failed");
  }

  return text;
}

export async function chatRoutes(app: FastifyInstance): Promise<void> {
  // Existing single message generation route
  app.post(
    "/api/chat",
    { preHandler: authMiddleware },
    async (request, reply) => {
      const userId = request.user!.userId;
      const { message, history } = request.body as {
        message: string;
        history?: { role: "user" | "model"; parts: { text: string }[] }[];
      };

      if (!message) {
        reply.status(400).send({ error: "Message is required" });
        return;
      }

      try {
        const db = getDb();
        const text = await generateGeminiResponse(
          userId,
          message,
          history || [],
          db,
          request.user!.username
        );
        return { text };
      } catch (err: any) {
        console.error("[chat] Gemini generation error:", err);
        reply.status(500).send({ error: "Failed to generate chat response: " + err.message });
      }
    }
  );

  // GET all chat sessions for the logged-in user
  app.get(
    "/api/chat/sessions",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const db = getDb();
        const sessions = await db
          .collection("chat_sessions")
          .find({ owner_id: userId })
          .sort({ timestamp: -1 })
          .toArray();

        return sessions.map((s) => ({
          id: s._id.toString(),
          title: s.title,
          messages: s.messages,
          timestamp: s.timestamp,
        }));
      } catch (error: any) {
        console.error("[chat] GET /api/chat/sessions error:", error);
        reply.status(500).send({ error: error.message || "Failed to fetch chat sessions" });
      }
    }
  );

  // POST create a new chat session
  app.post(
    "/api/chat/sessions",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const body = request.body as { id?: string; title?: string; messages?: any[] } | null;
        const db = getDb();

        const id = body?.id || new Date().getTime().toString() + "-" + Math.random().toString(36).substring(2, 9);
        const title = body?.title || "New Strategy Chat";
        const messages = body?.messages || [
          {
            id: "welcome",
            sender: "model",
            text: "Hello! I am your AI Poké Dueler Assistant, specialized in Gen 9 (Scarlet & Violet) PvP mechanics. Ask me to build a squad, analyze your active roster, or request counters for any Pokémon. Use slash commands like /suggest-team to start!",
            timestamp: Date.now(),
          },
        ];

        const doc = {
          _id: id as any,
          owner_id: userId,
          title,
          timestamp: Date.now(),
          messages,
        };

        await db.collection("chat_sessions").insertOne(doc);
        return {
          id: doc._id,
          title: doc.title,
          messages: doc.messages,
          timestamp: doc.timestamp,
        };
      } catch (error: any) {
        console.error("[chat] POST /api/chat/sessions error:", error);
        reply.status(500).send({ error: error.message || "Failed to create chat session" });
      }
    }
  );

  // PUT update chat session (e.g. title changes, messages updated/cleared)
  app.put(
    "/api/chat/sessions/:id",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { id } = request.params as { id: string };
        const body = request.body as { title?: string; messages?: any[] };
        const db = getDb();

        const updateDoc: any = {};
        if (body.title !== undefined) updateDoc.title = body.title;
        if (body.messages !== undefined) updateDoc.messages = body.messages;
        updateDoc.timestamp = Date.now();

        const result = await db.collection("chat_sessions").updateOne(
          { _id: id as any, owner_id: userId },
          { $set: updateDoc }
        );

        if (result.matchedCount === 0) {
          reply.status(404).send({ error: "Session not found" });
          return;
        }

        return { success: true };
      } catch (error: any) {
        console.error("[chat] PUT /api/chat/sessions error:", error);
        reply.status(500).send({ error: error.message || "Failed to update chat session" });
      }
    }
  );

  // POST send a message in a session and generate AI response
  app.post(
    "/api/chat/sessions/:id/messages",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { id } = request.params as { id: string };
        const { message } = request.body as { message: string };
        const db = getDb();

        if (!message) {
          reply.status(400).send({ error: "Message is required" });
          return;
        }

        const session = await db
          .collection("chat_sessions")
          .findOne({ _id: id as any, owner_id: userId });

        if (!session) {
          reply.status(404).send({ error: "Session not found" });
          return;
        }

        // Build history for Gemini
        const history = (session.messages || [])
          .filter((m: any) => m.id !== "welcome")
          .map((m: any) => ({
            role: m.sender === "user" ? "user" : "model",
            parts: [{ text: m.text }],
          }));

        // Generate response using core Gemini logic
        const aiText = await generateGeminiResponse(
          userId,
          message,
          history,
          db,
          request.user!.username
        );

        const userMsg = {
          id: Date.now().toString() + "-user",
          sender: "user",
          text: message,
          timestamp: Date.now(),
        };

        const suggestedTeam = extractSuggestedTeam(aiText);
        const cleanedText = cleanMessageText(aiText);

        const botMsg = {
          id: (Date.now() + 1).toString() + "-bot",
          sender: "model",
          text: cleanedText || aiText,
          timestamp: Date.now(),
          suggestedTeam,
        };

        const newMessages = [...(session.messages || []), userMsg, botMsg];
        const isDefaultTitle = session.title === "New Strategy Chat";
        const newTitle = isDefaultTitle
          ? message.length > 25
            ? message.substring(0, 22) + "..."
            : message
          : session.title;

        await db.collection("chat_sessions").updateOne(
          { _id: id as any, owner_id: userId },
          {
            $set: {
              title: newTitle,
              messages: newMessages,
              timestamp: Date.now(),
            },
          }
        );

        return {
          userMessage: userMsg,
          botMessage: botMsg,
          sessionTitle: newTitle,
        };
      } catch (error: any) {
        console.error("[chat] POST /api/chat/sessions/:id/messages error:", error);
        reply.status(500).send({ error: error.message || "Failed to process chat message" });
      }
    }
  );

  // DELETE a chat session
  app.delete(
    "/api/chat/sessions/:id",
    { preHandler: authMiddleware },
    async (request, reply) => {
      try {
        const userId = request.user!.userId;
        const { id } = request.params as { id: string };
        const db = getDb();

        const result = await db
          .collection("chat_sessions")
          .deleteOne({ _id: id as any, owner_id: userId });

        if (result.deletedCount === 0) {
          reply.status(404).send({ error: "Session not found" });
          return;
        }

        return { success: true };
      } catch (error: any) {
        console.error("[chat] DELETE /api/chat/sessions error:", error);
        reply.status(500).send({ error: error.message || "Failed to delete chat session" });
      }
    }
  );
}

import { FastifyInstance } from "fastify";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { authMiddleware } from "../middleware/auth.js";
import { getDb } from "../db/mongo.js";
import { config } from "../config.js";

export async function chatRoutes(app: FastifyInstance): Promise<void> {
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

      if (!config.geminiApiKey) {
        reply.status(500).send({
          error: "Gemini API key is not configured in .env file. Please define GEMINI_API_KEY.",
        });
        return;
      }

      try {
        const db = getDb();

        // 1. Retrieve profile data
        const player = await db.collection("players").findOne({ _id: userId as any });
        const username = player?.username || request.user!.username || "Trainer";
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
        const formattedTeams = teams.map((t) => ({
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

        const recentMatches = recentMatchesDocs.map((match) => {
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

        const topStandings = topPlayersDocs.map((player, index) => {
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

        return { text };
      } catch (err: any) {
        console.error("[chat] Gemini generation error:", err);
        reply.status(500).send({ error: "Failed to generate chat response: " + err.message });
      }
    },
  );
}

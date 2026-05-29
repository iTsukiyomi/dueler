import asyncio
import aiohttp
import os
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import traceback
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)


intents = discord.Intents.default()
intents.members = True
intents.message_content  = True

class Flame(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(';'),
            intents=intents,
            description='test',
            case_insensitive=True,
            owner_ids={853283237630967839, 839182501091344444},
            help_command=None
        )

    async def setup_hook(self):
        print('starting...')
        try:
            await self.load_extension('pokemonduel')
            await self.load_extension('admin')
            print('loaded pokeduel\nloaded admin')
        except Exception as e:
            print(e)

    async def on_ready(self):
        print(f'{self.user} logged in frfr ')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"missing arguments `{error.param}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"bro what")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("no perms bro")
        else:
            logging.error(f"unexpected error in {ctx.command}: {error}")
            await ctx.send(f"bruhh {error}")

# Ignore this stuff its for render to host the bot.

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

async def keep_alive():
    url = "https://dueler-wv0o.onrender.com"
    if not url:
        logging.warning("RENDER_URL not set, keep_alive disabled")
        return

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # pyrefly: ignore [bad-argument-type]
                async with session.get(url, timeout=10) as resp:
                    logging.info(f"Keep-alive ping: {resp.status}")
            except Exception as e:
                logging.error(f"Keep-alive failed: {e}")

            await asyncio.sleep(300)

async def main():
    threading.Thread(target=start_dummy_server, daemon=True).start()
    bot = Flame()
    asyncio.create_task(keep_alive())
    token = os.getenv("DISCORD_TOKEN")
    # pyrefly: ignore [bad-argument-type]
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())

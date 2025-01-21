import discord
from discord.ext import commands
from aiohttp import web
import asyncio

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_get('/status', self.handle_status)
        self.runner = None
        self.site = None
        self.loop = asyncio.get_event_loop()

        # Start the web server in the background
        self.loop.create_task(self.start_webserver())

    async def start_webserver(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 5045)  # Replace with your desired host/port
        await self.site.start()
        print("Webserver started on http://0.0.0.0:5045/status")

    async def handle_status(self, request):
        """Handle GET requests to /status"""
        data = {
            "status": "online",
            "guilds": len(self.bot.guilds)
        }
        return web.json_response(data)

    def cog_unload(self):
        """Cleanup when the cog is unloaded"""
        if self.site:
            self.loop.create_task(self.runner.cleanup())

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(StatusCog(bot))

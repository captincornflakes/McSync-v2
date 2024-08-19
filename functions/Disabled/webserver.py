import discord
from discord.ext import commands
from threading import Thread
from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

class JSONEditorWebServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_thread = Thread(target=self.run_webserver)
        self.web_thread.daemon = True
        self.web_thread.start()

    def run_webserver(self):
        app.run(host='0.0.0.0', port=5000)

    @app.route('/json/<filename>', methods=['GET'])
    def get_json_file(filename):
        """Endpoint to retrieve a JSON file."""
        filepath = f'datastores/{filename}.json'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({"error": "File not found"}), 404

    @app.route('/json/<filename>', methods=['POST'])
    def update_json_file(filename):
        """Endpoint to update a JSON file."""
        filepath = f'datastores/{filename}.json'
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        
        data = request.json
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return jsonify({"message": f"{filename}.json has been updated successfully."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @commands.command(name='webserver')
    async def webserver_status(self, ctx):
        """Check the status of the web server."""
        await ctx.send("Web server is running on port 5000. Use `/json/<filename>` to access the JSON files.")

# Register the Cog
async def setup(bot):
    await bot.add_cog(JSONEditorWebServer(bot))

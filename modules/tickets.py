import io
import discord
import yaml
import chat_exporter
from discord import Button, ActionRow, ButtonStyle, app_commands
from discord.ext import commands
from discord.utils import get
from database import Database
from utils import remove_command_message, check_permissions

db = Database(False)
config = yaml.safe_load(open("modules/ticketsConfig.yml", 'r', encoding="utf-8"))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        db.check_create_table("tickets", "id INT AUTO_INCREMENT PRIMARY KEY, ticket_channel_id VARCHAR(64),"
                                         " ticket_category VARCHAR(255), creator_id VARCHAR(64),"
                                         " is_closed BOOLEAN, creation_date DATE")
        print('Tickets workanti!')

    @commands.hybrid_command(name="ticketsgen", with_app_command=True,
                             description="crea L'embed per generare ticket")
    async def ticketsgen(self, ctx):
        role_identificator = config.get("ticket-creation-admin-role")
        if await check_permissions(ctx.author, role_identificator):
            await self.create_generator(ctx)
            await remove_command_message(ctx.message)

import asyncio
import os
import discord
import yaml
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from database import Database
from utils import remove_command_message

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='.', intents=intents)
config = yaml.safe_load(open("config.yml", 'r', encoding="utf-8"))
db = Database()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(config.get("bot-activity")))
    print("sincronizzazione dei comandi...")
    await bot.tree.sync()
    print('Bot pronto)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        if config.get("remove-unknown-commands"):
            await remove_command_message(ctx.message)
        embed_conf = config.get("command-not-found-embed")
        if embed_conf.get("enabled"):
            embed = discord.Embed(title=embed_conf.get("title"),
                                  description=embed_conf.get("description"),
                                  color=embed_conf.get("color"))
            embed.set_footer(text=embed_conf.get("footer"))
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=10)
            return
    raise error

modules = []

for filename in os.listdir('./modules'):
    if filename.endswith('.py'):
        modules.append("modules." + filename[:-3])

async def main():
    for extension in modules:
        await bot.load_extension(extension)



if __name__ == '__main__':
    asyncio.run(main())

bot.run(config.get("bot-token"))

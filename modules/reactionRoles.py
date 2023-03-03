import discord
import yaml
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from database import Database
from utils import remove_command_message, check_permissions

db = Database(False)
config = yaml.safe_load(open("modules/reactionRolesConfig.yml", 'r', encoding="utf-8"))

class ReactionRoles(commands.Cog):

    def __init__(self, bot):
        db.check_create_table("reactionRoles",
                              "id INT AUTO_INCREMENT PRIMARY KEY, message_id VARCHAR(64),"
                              "selector VARCHAR(64), is_active BOOL DEFAULT 1")
        print('ReactionRoles workanti')
        self.bot = bot

    @commands.hybrid_command(description="Crea un nuovo selettore di ruolo")
    @app_commands.rename(arg='selector_name')
    @app_commands.describe(arg='Selector name defined in config')
    async def reactionroles(self, ctx, arg):
        if not await check_permissions(ctx.author, config.get("selector-creation-admin-role")):
            return  # Exit if user doesn't have enough perms
        for selector in config.get("selectors"):
            if selector == arg:
                selector_config = config.get("selectors").get(selector)
                embed = discord.Embed(title=selector_config.get("embed-title"),
                                      description=selector_config.get("embed-description"),
                                      colour=selector_config.get("embed-color"))
                embed.set_footer(text=selector_config.get("embed-footer"))
                if selector_config.get("type") == "menu":
                    view = discord.ui.View()
                    view.add_item(RoleSelect(selector_config.get("options"), selector_config.get("select-menu-title"), selector, selector_config.get("only-one-role")))
                    reply_message = await ctx.reply("...")
                    await ctx.channel.send(embed=embed, view=view)
                    await reply_message.delete()
                else:
                    reply_message = await ctx.reply("...")
                    message = await ctx.channel.send(embed=embed)
                    await reply_message.delete()
                    db.insert("reactionRoles", "message_id, selector", f"{str(message.id)}, '{str(selector)}'")
                    for role_option in selector_config.get("options"):
                        emoji = selector_config.get("options").get(role_option).get("emoji")
                        await message.add_reaction(emoji)
                return
        error_embed = discord.Embed(title="Selettore non trovato!",
                                    description="Il selettore richiesto non è stato trovato nella configurazione.",
                                    colour=0xff0000)
        await ctx.reply(embed=error_embed)
        await remove_command_message(ctx.message)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        custom_id = interaction.data.get("custom_id")
        if custom_id is None or not custom_id.startswith("role_select"):
            return
        await interaction.response.defer(thinking=False)
        user = interaction.user
        selector = custom_id.split("role_select")[1]
        selector_conf = config.get("selectors").get(selector)
        values = interaction.data.get("values")
        for option in selector_conf.get("options"):
            option_conf = selector_conf.get("options").get(option)
            role_identificator = option_conf.get("role")
            role = await self.get_role(role_identificator, interaction.guild)
            if role is None:
                continue
            if option in values:    # Roles to add
                required_role = option_conf.get("required-role")
                if required_role is not None:
                    required_r = await self.get_role(required_role, interaction.guild)
                    if required_r is None:
                        return
                    if required_r not in user.roles:
                        embed_conf = config.get("another-role-required-embed")
                        embed = discord.Embed(
                            title=embed_conf.get("embed-title").replace("{user}", user.name),
                            description=embed_conf.get("embed-description").replace("{required_role}",
                                                                                    required_r.name),
                            color=embed_conf.get("embed-color"))
                        embed.set_footer(text=embed_conf.get("embed-footer"))
                        if str.lower(embed_conf.get("send-to")) == "dm":
                            await user.send(embed=embed)
                        elif str.lower(embed_conf.get("send-to")) == "channel":
                            msg = await interaction.response.send_message(embed=embed, ephemeral=True)
                            await msg.delete(delay=10)
                        return
                if not role in user.roles:
                    await self.add_user_role(role, interaction.channel, user)

            else:  # Roles to remove
                if role in user.roles:
                    await self.remove_user_role(role, interaction.channel, user)


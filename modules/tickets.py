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


    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        channel = interaction.channel
        custom_id = interaction.data.get("custom_id")
        if custom_id is None:
            return
        # --- Button is for closing ticket ---
        # Without confirmation
        if custom_id == "tickets_close_ticket":
            if config.get("require-close-confirmation") is True:
                await self.confirm_close_ticket(interaction)
            else:
                await self.close_ticket(channel, False)
            return
        # With confirmation
        if custom_id == "tickets_confirm_close_ticket":
            await self.close_ticket(channel, False)
            return

        # --- Button is for creating new ticket ---
        for category in config.get("categories"):
            if custom_id == "tickets_" + category:
                category_conf = config.get("categories").get(category)
                user = interaction.user
                guild = interaction.guild
                # Check that user has role required to create the ticket in this category
                role_identificator = category_conf.get("required-role")
                if role_identificator is not None:
                    if isinstance(role_identificator, int):
                        required_role = discord.utils.get(guild.roles, id=role_identificator)
                    else:
                        required_role = discord.utils.get(guild.roles, name=role_identificator)
                    if required_role not in user.roles:
                        # Send embed with info about missing role
                        embed_conf = config.get("missing-role-embed")
                        embed_desc = embed_conf.get("embed-description").replace("{role}", required_role.mention)
                        dembed = discord.Embed(title=embed_conf.get("embed-title"),
                                               description=embed_desc,
                                               color=embed_conf.get("embed-colour"))
                        dembed.set_footer(text=embed_conf.get("embed-footer"))
                        await interaction.response.send_message(ephemeral=True, embed=dembed)
                        return  # Do not create ticket and exit

                if db.get_count("tickets", f"creator_id={str(user.id)} AND is_closed=0") < config.get(
                        "maximum-tickets-per-user"):
                    # User can create ticket
                    # Create the ticket channel
                    role_identificator = category_conf.get("admin-role")
                    if isinstance(role_identificator, int):
                        admin_role = discord.utils.get(guild.roles, id=role_identificator)
                    else:
                        admin_role = discord.utils.get(guild.roles, name=role_identificator)
                    if not admin_role:  # If admin role is not set up
                        error = "Si è verificato un errore durante il tentativo di ottenere **admin-role** per categoria di ticket." \
                                " Per favore, controlla la tua configurazione e riprova."
                        print(error)
                        await self.send_error_message(interaction.channel, error)
                        return
                    cat = discord.utils.get(guild.categories, name=config.get("ticket-channel-category"))
                    if not cat:  # If category doesn't exist
                        error = "Si è verificato un errore durante il tentativo di ottenere **category** per canale ticket." \
                                " Per favore, controlla la tua configurazione e riprova."
                        print(error)
                        await self.send_error_message(interaction.channel, error)
                        return
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True),
                        user: discord.PermissionOverwrite(read_messages=True),
                        admin_role: discord.PermissionOverwrite(read_messages=True)
                    }
                    channel_name = config.get("ticket-channel-name-format")
                    channel_name = channel_name.replace("{ticket_count}", str(db.get_next_auto_increment("tickets")))
                    channel_name = channel_name.replace("{creator}", user.name)
                    channel_name = channel_name.replace("{category_name}", category_conf.get("name"))
                    channel = await guild.create_text_channel(channel_name,
                                                              category=cat, overwrites=overwrites)
                    db.insert("tickets", "ticket_channel_id, ticket_category, creator_id, is_closed, creation_date",
                              "'" + str(channel.id) + "', '" + str(category) + "', '" + str(user.id) + "', 0, NOW()")
                    # Create management embed in the ticket
                    embed_conf = config.get("ticket-management-embed")
                    embed_desc = embed_conf.get("embed-description").replace("{instructions}",
                                                                             category_conf.get("instructions"))
                    membed = discord.Embed(title=embed_conf.get("embed-title").replace("{channel-name}", channel.name),
                                           description=embed_desc,
                                           colour=embed_conf.get("embed-colour"))
                    membed.set_footer(text=embed_conf.get("embed-footer"))
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label=embed_conf.get("close-button"), custom_id="tickets_close_ticket", style=ButtonStyle.gray))
                    await channel.send(embed=membed, view=view)
                    # Ping admins in the ticket channel
                    if config.get("ping-admin-role-on-creation"):
                        msg = await channel.send(f"{admin_role.mention}")
                        await msg.delete()
                    # Send embed to generator that the ticket has been created and where
                    embed_conf = config.get("ticket-created-embed")
                    dembed = discord.Embed(title=embed_conf.get("embed-title"),
                                           description=embed_conf.get("embed-description").replace("{channel}",
                                                                                                   channel.mention),
                                           colour=embed_conf.get("embed-colour"))
                    dembed.set_footer(text=embed_conf.get("embed-footer"))
                    await interaction.response.send_message(embed=dembed, ephemeral=True)
                    print(f"Ticket creato per {user.name}")

                else:
                    # User has too many tickets
                    embed_conf = config.get("too-many-tickets-embed")
                    embed = discord.Embed(title=embed_conf.get("embed-title"),
                                          description=embed_conf.get("embed-description"),
                                          colour=embed_conf.get("embed-colour"))
                    embed.set_footer(text=embed_conf.get("embed-footer"))
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    print(f"Impossibile creare il ticket per {interaction.user.name}, l'utente ha troppi tickets")


    @commands.Cog.listener()
    async def on_message(self, message):
        if not config.get("ping-admin-role-on-user-response"):
            return
        if db.check_contains("tickets", "ticket_channel_id", str(message.channel.id))\
                and db.check_contains("tickets", "creator_id", str(message.author.id)):
            category = db.get_value_general("tickets", "ticket_category",
                                            f"ticket_channel_id={str(message.channel.id)} AND creator_id={str(message.author.id)}")
            role_identificator = config.get("categories").get(category).get("admin-role")
            if isinstance(role_identificator, int):
                admin_role = discord.utils.get(message.guild.roles, id=role_identificator)
            else:
                admin_role = discord.utils.get(message.guild.roles, name=role_identificator)
            msg = await message.channel.send(f"{admin_role.mention}")
            await msg.delete()


    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if db.check_contains("tickets", "ticket_channel_id", str(channel.id)):
            if not db.get_value_general("tickets", "is_closed", f"ticket_channel_id={channel.id}"):
                await self.close_ticket(channel, True)
                print("Ticket chiusura forzata, il canale è stato eliminato!")


    @commands.hybrid_command(description="Chiude il ticket")
    async def close(self, ctx):
        channel = ctx.message.channel
        if db.check_contains("tickets", "ticket_channel_id", str(channel.id)):
            if not db.get_value_general("tickets", "is_closed", f"ticket_channel_id={channel.id}"):
                await self.close_ticket(channel, False)



    @staticmethod
    async def confirm_close_ticket(interaction):
        embed_conf = config.get("confirm-close-embed")
        embed = discord.Embed(title=embed_conf.get("embed-title"),
                              description=embed_conf.get("embed-description"),
                              color=embed_conf.get("embed-colour"))
        embed.set_footer(text=embed_conf.get("embed-footer"))
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=embed_conf.get("confirm-button"), custom_id="tickets_confirm_close_ticket", style=ButtonStyle.gray))
        await interaction.response.send_message(embed=embed,
                                  ephemeral=True,
                                  view=view)

    async def close_ticket(self, channel, force_closed):
        ticket_id = db.get_id("tickets", "ticket_channel_id=" + str(channel.id))
        db.update_data("tickets", "is_closed", "1", f"id={str(ticket_id)}")
        if not force_closed:
            if config.get("send-transcription"):
                await self.create_transcript(ticket_id, channel)
            await channel.delete()
        print(f"Ticket {str(ticket_id)} chiuso.")

    async def create_transcript(self, ticket_id, channel):
        try:
            transcript = await chat_exporter.export(channel)
            if transcript is None:
                return
        except Exception as e:
            print("Si è verificato un errore durante il tentativo di creare la trascrizione del ticket:")
            print(e)
            return
        ticket_creator = await self.bot.fetch_user(db.get_value_general("tickets", "creator_id", f"id={ticket_id}"))
        if ticket_creator:
            try:
                await ticket_creator.send(content=str(config.get("transcript-description")),
                                          file=discord.File(io.BytesIO(transcript.encode()),
                                                            filename=f"{channel.name}.html", ))
            except Exception:
                print(f"Impossibile inviare la trascrizione del ticket all'autore del ticket. ({channel.name})")
        ticket_log_channel = get(self.bot.get_all_channels(), id=config.get("transcript-channel"))
        if ticket_log_channel:
            await ticket_log_channel.send(
                file=discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}.html"))

    async def create_generator(self, ctx):
        econfig = config.get("ticket-creator-embed")
        embed = discord.Embed(title=econfig.get("embed-title"),
                              description=econfig.get("embed-description"),
                              colour=econfig.get("embed-colour"))
        embed.set_footer(text=econfig.get("embed-footer"))

        view = discord.ui.View()
        for category in config.get("categories"):
            button_conf = config.get("categories").get(category)
            b_emoji = button_conf.get("emoji")
            if b_emoji == '':
                view.add_item(discord.ui.Button(label=button_conf.get("name"), custom_id="tickets_" + category, style=ButtonStyle.gray))
            else:
                view.add_item(discord.ui.Button(label=button_conf.get("name"), emoji=b_emoji, custom_id="tickets_" + category, style=ButtonStyle.gray))
        await ctx.reply(embed=embed, view=view)
        print("Ticket generator created!")

    @staticmethod
    async def send_error_message(channel, error_message):
        embed = discord.Embed(title="Bot ERROR", description=error_message, colour=0xff0000)
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))

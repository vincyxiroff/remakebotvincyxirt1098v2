import discord


async def remove_command_message(message):
    if message.type != discord.MessageType.default:
        return
    await message.delete()


async def check_permissions(member: discord.Member, required_role):
    if member.guild_permissions.administrator:
        return True  # Admins dovrebbero essere sempre in grado di eseguire tutto
    if required_role is None:   # There is a requirement for specific role to use the command
        return False

    guild = member.guild
    if isinstance(required_role, int):
        role = discord.utils.get(guild.roles, id=required_role)
    else:
        role = discord.utils.get(guild.roles, name=required_role)
    if role is None:
        print(f"Role {required_role} was not found on your server,"
              f" please, check your configuration!")
        return False    # The role does not exist
    if role not in member.roles:
        return False    # User does not have the role
    return True     # Else user has the permissions

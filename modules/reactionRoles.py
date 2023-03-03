import discord
import yaml
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from database import Database
from utils import remove_command_message, check_permissions

db = Database(False)
config = yaml.safe_load(open("modules/reactionRolesConfig.yml", 'r', encoding="utf-8"))


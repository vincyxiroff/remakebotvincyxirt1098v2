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

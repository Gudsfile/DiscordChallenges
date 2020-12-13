import os
import logging
from tinydb import TinyDB
from discord.ext.commands import Bot

# config
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
DISCORD_PREFIX = ';'
DB_FILE = 'data.json'
DB_TABLE_USERS = 'users'
DB_TABLE_CHALLENGES = 'challenges'
LOGGER_LEVEL = logging.DEBUG
LOGGER_FILE = 'discord.log'
LOGGER_FORMAT = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
REMINDER_FREQUENCY = 24  # hours
CHALLENGE_DELAY = 7  # days
BLURPLE = 0x4e5d94
MAX_PER_PAGE = 9
DATE_FORMAT = '%d/%m/%Y'
POINT_FOR_REFUSAL = -2
POINT_FOR_SUCCESS = 1
POINT_FOR_FAILURE = 0

# Tiny db
db = TinyDB(DB_FILE)
db_users = db.table(DB_TABLE_USERS)
db_challenges = db.table(DB_TABLE_CHALLENGES)

# Discord bot
bot = Bot(command_prefix=DISCORD_PREFIX,
          description='''VERSION 1.0.0 - Bot by t0''',
          self_bot=False)

# Logger
logger = logging.getLogger('discord')
logger.setLevel(LOGGER_LEVEL)
formatter = logging.Formatter(LOGGER_FORMAT)
fileHandler = logging.FileHandler(filename=LOGGER_FILE, encoding='utf-8', mode='w')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

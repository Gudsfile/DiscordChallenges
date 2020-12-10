import logging
import os
import json

import discord
from discord import Game, Embed, Color, Status, ChannelType
from discord.ext import commands
from discord.ext.commands import Bot
from tinydb import TinyDB, Query

# Config
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
DISCORD_PREFIX = '$'
DB_FILE = 'data.json'
DB_TABLE_USERS = 'users'
DB_TABLE_CHALLENGES = 'challenges'
LOGGER_LEVEL = logging.INFO
LOGGER_FILE = 'discord.log'

# Tiny db
db = TinyDB(DB_FILE)
users = db.table(DB_TABLE_USERS)
challenges = db.table(DB_TABLE_CHALLENGES)

# Discord bot
bot = Bot(command_prefix=DISCORD_PREFIX,
          description='''Bot by t0''', self_bot=False)

# Logger
logger = logging.getLogger('discord')
logger.setLevel(LOGGER_LEVEL)
formatter = logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s')
fileHandler = logging.FileHandler(
    filename=LOGGER_FILE, encoding='utf-8', mode='w')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(formatter)
# logger.addHandler(consoleHandler)


@bot.command()
async def inscription(ctx):
    # TODO empecher l'inscription si déjà inscris
    users.insert({'type': 'users', 'id': ctx.author.id, 'challenge': None,
                  'timestamp': None, 'last_challenges': list(), 'score': 0})
    await ctx.send('Soit le meilleur garçon.')


@bot.command()
async def ajout(ctx, challenge):
    # TODO empêcher l'ajout d'un défi si déjà enregistré
    challenges.insert(
        {'type': 'challenges', 'author': ctx.author.id, 'description': challenge})
    await ctx.send('Voila mon ptit pote le défi a été ajouté !')


@bot.command()
async def info(ctx):
    # TODO afficher le défi de l'auteur
    # TODO afficher le défi de la personne mentionnée
    pass


@bot.command()
async def defis(ctx):
    e = discord.Embed(color=discord.Color.blurple(), description='')
    for challenge in iter(challenges):
        e.description += challenge['description'] + '\n'
    await ctx.send(embed=e)


@bot.command()
async def joueurs(ctx):
    e = discord.Embed(color=discord.Color.blurple(), description='')
    for user in iter(users):
        e.description += user['id'] + '\n'
    await ctx.send(embed=e)


# TODO attribution d'un défi
# TODO évaluation des defis
# TODO une durée aux défis ?
# TODO suppression d'un defi
# TODO help

logger.info("Starting up and logging in...")
bot.run(DISCORD_TOKEN, bot=True)
logger.info("Completion timestamp")
logger.info("Done!")

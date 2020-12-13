from datetime import datetime, timedelta
from itertools import zip_longest
import json
import logging
import os
from random import randint

import discord
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Bot
from discord.ext.commands.errors import CommandInvokeError
from tinydb import TinyDB, Query, where
from tinydb.operations import set, add

# Config
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
BLURPLE = 0x4e5d94  # burple
MAX_PER_PAGE = 9  # elements per page
DATE_FORMAT = '%d/%m/%Y'  # date format
REFUSE_POINT = -2
SUCCESS_POINT = 1
FAILURE_POINT = 0

# Tiny db
db = TinyDB(DB_FILE)
db_users = db.table(DB_TABLE_USERS)
db_challenges = db.table(DB_TABLE_CHALLENGES)

# Discord bot
bot = Bot(command_prefix=DISCORD_PREFIX,
          description='''VERSION 1.0.0 - Bot by t0''', self_bot=False)

# Logger
logger = logging.getLogger('discord')
logger.setLevel(LOGGER_LEVEL)
formatter = logging.Formatter(LOGGER_FORMAT)
fileHandler = logging.FileHandler(filename=LOGGER_FILE,
                                  encoding='utf-8', mode='w')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)


@bot.event
async def on_ready():
    logger.info("Bot ready")


@bot.command(name='start', aliases=['inscription'])
async def start_game(ctx):
    """
    👤 Commencer à s'épanouir.

        usage: [;]start|inscription
    """
    user_id = ctx.author.id

    if db_users.search(where('id') == user_id):
        await ctx.send(f"<@{user_id}> mais ? Toi déjà être inscris abruti...")
        return False

    db_users.insert({
        'type': 'users',
        'id': user_id,
        'challenge': None,
        'timestamp_start': None,
        'timestamp_end': None,
        'last_challenges': list(),
        'score': 0
    })
    await ctx.send(f"<@{user_id}> gooooooooooooooooo.\nAjoute des défis avec `{DISCORD_PREFIX}ajout` ou récupère en un avec `{DISCORD_PREFIX}defi`.\n`{DISCORD_PREFIX}help` pour plus d'aide.")


@bot.command(name='stop', aliases=['desinscription'])
async def stop_game(ctx):
    """
    👤 Mettre fin à son épanouissement.

        usage: [;]stop|desinscription
    """
    # TODO suppression des défis
    user_id = ctx.author.id

    if not db_users.search(where('id') == user_id):
        await ctx.send(f"<@{user_id}> mais ? Toi pas être inscris abruti...")
        return False

    db_users.remove(where('id') == user_id)
    await ctx.send(f"Aller bye bye <@{user_id}>.")


@bot.command(name='add', aliases=['a', 'ajout'])
async def add_challenge(ctx, *args):
    """
    🃏 Ajoute un défi.

        usage: [;]add|a|ajout <mon défi>
    """
    # TODO ajouter plusieurs défis simultanément
    challenge = ' '.join(args)

    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f"Wow <@{ctx.author.id}> fais attention ! Garde les défis secrets et ajoute les en DM bg.")
        await ctx.author.send("Pour ajouter un défi utilise la commande `ajout <le defi en question>` dans cette conversation.")
        await ctx.message.delete()
        return False

    if not challenge:
        await ctx.send("Sérieux ? Tu me demandes d'enregistrer le vide là.")
        return False

    if db_challenges.search(where('description') == challenge):
        await ctx.send("HepHepHep il y est déjà ce défi boloss.")
        return False

    db_challenges.insert({
        'type': 'challenges',
        'author': ctx.author.id,
        'description': challenge
    })
    await ctx.send("Voila mon ptit pote le défi a été ajouté !")


@bot.command(name='remove', aliases=['r', 'retrait'])
async def remove_challenge(ctx, challenge_id: int):
    """
    🃏 Supprime un défi.

        usage: [;]remove|r|retrait <défi id>
    """
    challenge = db_challenges.get(doc_id=challenge_id)

    if not challenge:
        await ctx.send("T'es fou gadjo il existe po ton défi...")
        return False

    if not challenge['author'] == ctx.author.id:
        await ctx.send("Ce n'est pas ton défi tu ne peux pas le supprimer.")
        return False

    db_challenges.remove(doc_ids=[challenge.doc_id])
    await ctx.send("Trop dur pour toi ce défi ? Le vla retiré.")


@bot.command(name='info', aliases=['i'])
async def info(ctx):
    """
    👤 Récupérer les informations joueur.

        usage: [;]info|i
    """
    # TODO afficher le défi de la personne mentionnée
    # TODO embed info
    user_id = ctx.author.id

    Users = Query()
    db_user = db_users.get(Users.id == user_id)
    dc_user = await bot.fetch_user(user_id)
    user_name = dc_user.name

    if not db_user:
        await ctx.send(f"Eh oh pourquoi {user_name} tu ne joue pas ?")
        return False

    user_challenge_id = db_user['challenge']

    if user_challenge_id is None:
        await ctx.send(f"{user_name} tu n'a pas de défi.")
        return False

    user_challenge_description = db_challenges.all(
    )[user_challenge_id]['description']

    await ctx.send(f"<@{user_id}> tu as pour défi de `{user_challenge_description}`, bonne chance gros bg.")


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@bot.command(name='challenges', aliases=['lc', 'defis'])
async def list_challenges(ctx, page_num: int = 0):
    """
    🃏 Lister les défis.

        usage: [;]challenges|lc|defis <numero de page>
    """
    # TODO bug 0 défis
    # TODO bug pagination
    # TODO afficher que ceux de l'auteur dès la recherche
    # inspiré de
    # https://stackoverflow.com/questions/61787520/i-want-to-make-a-multi-page-help-command-using-discord-py

    contents = [chunk for chunk in grouper(db_challenges, MAX_PER_PAGE)]
    last_page = len(contents) - 1
    cur_page = page_num - 1 if page_num > 0 and page_num - 1 <= last_page else 0

    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Je t'envoie ça en DM mi amor.")

    async def page_embed(challenges, cur_page, last_page):
        count = cur_page * MAX_PER_PAGE
        embed = Embed(title='Liste des défis', color=BLURPLE)
        for challenge in challenges:
            if not challenge:
                continue
            dc_user = await bot.fetch_user(challenge['author'])
            embed.add_field(name=challenge['description'] if challenge['author'] == ctx.author.id else '-- SECRET --',
                            value=f"ID: {challenge.doc_id}, Auteur: {dc_user.name}",
                            inline=True)
            count += 1
        embed.set_footer(text=f"Page {cur_page+1} sur {last_page+1}")
        return embed

    page = await page_embed(contents[cur_page], cur_page, last_page)
    message = await ctx.author.send(embed=page)
    # getting the message object for editing and reacting

    if last_page >= 10:
        await message.add_reaction('⏮')
    if last_page >= 5:
        await message.add_reaction('⏪')
    if last_page >= 1:
        await message.add_reaction('◀️')
    if last_page >= 1:
        await message.add_reaction('▶️')
    if last_page >= 5:
        await message.add_reaction('⏩')
    if last_page >= 10:
        await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️', '⏩', '⏪', '⏭', '⏮']
        # This makes sure nobody except the command sender can interact with the "menu"

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)
            # waiting for a reaction to be added - times out after x seconds, 60 in this

            if str(reaction.emoji) == '▶️' and cur_page != last_page:
                cur_page += 1
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '◀️' and cur_page >= 1:
                cur_page -= 1
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏩' and cur_page <= last_page - 5:
                cur_page += 5
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏪' and cur_page >= 5:
                cur_page -= 5
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏭' and cur_page <= last_page - 10:
                cur_page += 10
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏮' and cur_page >= 10:
                cur_page -= 10
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            else:
                await message.remove_reaction(reaction, user)
                # removes reactions if the user tries to go forward on the last page or
                # backwards on the first page
        except Exception as err:
            logger.warning('Timeout maybe (defis)')
            # await message.delete()
            break


@bot.command(name='players', aliases=['lp', 'joueurs'])
async def list_players(ctx, page_num: int = 0):
    """
    👤 Lister les joueurs.

        usage: [;]players|lp|joueurs <numero de page>
    """
    # inspiré de
    # https://stackoverflow.com/questions/61787520/i-want-to-make-a-multi-page-help-command-using-discord-py

    MAX_PER_PAGE = 9

    contents = [chunk for chunk in grouper(db_users, MAX_PER_PAGE)]
    last_page = len(contents) - 1
    cur_page = page_num - 1 if page_num > 0 and page_num - 1 <= last_page else 0

    async def page_embed(players, cur_page, last_page):
        count = cur_page * MAX_PER_PAGE
        embed = Embed(title='Liste des joueurs', color=BLURPLE)
        for player in players:
            if not player:
                continue
            dc_user = await bot.fetch_user(player['id'])

            # Get challenge description
            challenge_description = '/'
            if player['challenge']:
                challenge = db_challenges.get(doc_id=player['challenge'])
                challenge_description = challenge['description'] if challenge else '/'

            embed.add_field(name=dc_user.name,
                            value=f"Défi: `{challenge_description}`\nScore: `{player['score']}`",
                            inline=True)
            count += 1
        embed.set_footer(text=f"Page {cur_page+1} sur {last_page+1}")
        return embed

    page = await page_embed(contents[cur_page], cur_page, last_page)
    message = await ctx.send(embed=page)
    # getting the message object for editing and reacting

    if last_page >= 10:
        await message.add_reaction('⏮')
    if last_page >= 5:
        await message.add_reaction('⏪')
    if last_page >= 1:
        await message.add_reaction('◀️')
    if last_page >= 1:
        await message.add_reaction('▶️')
    if last_page >= 5:
        await message.add_reaction('⏩')
    if last_page >= 10:
        await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️', '⏩', '⏪', '⏭', '⏮']
        # This makes sure nobody except the command sender can interact with the "menu"

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)
            # waiting for a reaction to be added - times out after x seconds, 60 in this

            if str(reaction.emoji) == '▶️' and cur_page != last_page:
                cur_page += 1
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '◀️' and cur_page >= 1:
                cur_page -= 1
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏩' and cur_page <= last_page - 5:
                cur_page += 5
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏪' and cur_page >= 5:
                cur_page -= 5
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏭' and cur_page <= last_page - 10:
                cur_page += 10
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏮' and cur_page >= 10:
                cur_page -= 10
                page = await page_embed(contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                await message.remove_reaction(reaction, user)

            else:
                await message.remove_reaction(reaction, user)
                # removes reactions if the user tries to go forward on the last page or
                # backwards on the first page
        except Exception as err:
            logger.warning('Timeout maybe (joueurs)')
            # await message.delete()
            break


@bot.command(name='get', aliases=['g', 'defi'])
async def get_challenge(ctx):
    """
    🃏 Obtenir un défi.

        usage: [;]get|g|defi
    """
    # TODO interdire de le faire en privé
    # TODO empêcher si déjà un défi
    user_id = ctx.author.id

    if db_users.get(where('id') == user_id)['challenge']:
        await ctx.send(f"Tu as déjà un défi champion.\nS'il est terminé va le valider avec `{DISCORD_PREFIX}evaluation`.")
        return False

    if len(challenges) < 1:
        await ctx.send("Il n'y aucun défi dans la liste...")
        return False

    # tirage du défi
    challenge_id = randint(0, len(challenges) - 1)
    challenge = db_challenges.all()[challenge_id]
    challenge_description = challenge['description']

    # message
    message = await ctx.send(f"<@{user_id}> le defi `{challenge_description}` t'as été attribué es-tu partant(e) ? (-2 points si tu es faible)")
    await message.add_reaction('👍')
    await message.add_reaction('👎')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)

            if str(reaction.emoji) == '👍':
                # définition des dates
                start = datetime.now()
                end = start + timedelta(days=CHALLENGE_DELAY)
                challenge_start_date = start.strftime(DATE_FORMAT)
                challenge_end_date = end.strftime(DATE_FORMAT)

                # attribution du défi
                db_users.update(set('challenge', challenge_id),
                             where('id') == user_id)
                db_users.update(
                    set('timestamp_start', start.timestamp()), where('id') == user_id)
                db_users.update(set('timestamp_end', end.timestamp()),
                             where('id') == user_id)

                # communication
                await message.edit(content=f"Défi accepté. \n<@{user_id}> tu vas devoir `{challenge_description}` du {challenge_start_date} au {challenge_end_date}.\nC'est irrévocable.")
                await message.remove_reaction(reaction, user)
                break

            elif str(reaction.emoji) == '👎':
                # perte de point
                db_users.update(add('score', REFUSE_POINT),
                             where('id') == user_id)

                # communication
                await message.edit(content=f"Défi refusé.")
                await message.remove_reaction(reaction, user)
                break
        except Exception as err:
            logger.warning('Timeout maybe (defi)')
            await message.delete()
            break


@bot.command(name='validate',aliases=['v', 'valider'])
async def validate_challenge(ctx):
    """
    🃏 Terminer son défi.

        usage: [;]validate|v|valider
    """
    user_id = ctx.author.id

    db_user = db_users.get(where('id') == user_id)

    if not db_user:
        await ctx.send(f"<@{user_id}> tu n'as pas démaré ta marche vers l'épanouissement.\nCommence avec `{DISCORD_PREFIX}inscription.`")

    if not db_user['challenge']:
        await ctx.send(f"<@{user_id}> tu n'as pas encore de défi...")
        return False

    timestamp_end = datetime.fromtimestamp(db_user['timestamp_end'])
    if datetime.now().date() < timestamp_end.date():
        await ctx.send(f"Non non non, <@{user_id}> ton défi prendra fin le {timestamp_end.strftime(DATE_FORMAT)}")
        return False

    user_challenge_id = db_user['challenge']
    user_challenge_description = db_challenges.all(
    )[user_challenge_id]['description']

    message = await ctx.send(f"Alors <@{user_id}> as tu réussi ton défi ?\nPour rappel celui-ci était `{user_challenge_description}`.")
    await message.add_reaction('👍')
    await message.add_reaction('👎')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)

            if str(reaction.emoji) == '👍':
                # retrait du défi
                db_users.update(set('challenge', None), where('id') == user_id)
                db_users.update(set('timestamp_start', None),
                             where('id') == user_id)
                db_users.update(set('timestamp_end', None),
                             where('id') == user_id)
                db_users.update(add('score', SUCCESS_POINT),
                             where('id') == user_id)

                # communication
                await ctx.send(content=f"Bien joué <@{user_id}>, trop fort(e).")
                break

            elif str(reaction.emoji) == '👎':
                # retrait du défi
                db_users.update(set('challenge', None), where('id') == user_id)
                db_users.update(set('timestamp_start', None),
                             where('id') == user_id)
                db_users.update(set('timestamp_end', None),
                             where('id') == user_id)
                db_users.update(add('score', FAILURE_POINT),
                             where('id') == user_id)

                # communication
                # TODO emoji happy mask face
                await ctx.send(content=f"Pas grave <@{user_id}>, tu feras mieux la prochaine fois ! :happy_mask_face:")
        except Exception as err:
            logger.warning('Timeout maybe (evaluation)')
            break


@tasks.loop(hours=REMINDER_FREQUENCY)
async def reminder():
    now = datetime.now().date()

    for db_user in db_users.all():
        if not db_user['challenge']:
            continue
        timestamp_end = datetime.fromtimestamp(db_user['timestamp_end'])
        if (timestamp_end.date() - now).days < 1:
            dc_user = await bot.fetch_user(db_user['id'])
            await dc_user.send("N'oublie pas ton défi :p")

# TODO une durée aux défis ? score ?
# TODO listes de phrases
# TODO factoriser / réorganiser
# TODO Plusieurs phrases pour un même défis avec l’analyse (liste de description)
# TODO Notation d’un défis pour prévenir de ceux trop nuls
# TODO bdd multi guild/channel
# 🚧

reminder.start()

logger.info("Starting up and logging in...")
bot.run(DISCORD_TOKEN, bot=True)
logger.info("Completion timestamp")
logger.info("Done!")

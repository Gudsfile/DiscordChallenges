from datetime import datetime, timedelta
from itertools import zip_longest
import json
import logging
import os
from random import randint

from discord import Embed
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
LOGGER_LEVEL = logging.INFO
LOGGER_FILE = 'discord.log'
LOGGER_FORMAT = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
CHALLENGE_DELAY = 7
BLURPLE = 0x4e5d94
MAX_PER_PAGE = 9
DATE_FORMAT = '%d/%m/%Y'
REFUSE_POINT = -2

# Tiny db
db = TinyDB(DB_FILE)
users = db.table(DB_TABLE_USERS)
challenges = db.table(DB_TABLE_CHALLENGES)

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
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(formatter)
# logger.addHandler(consoleHandler)


@bot.command(aliases=['start'])
async def inscription(ctx):
    """
    👤 Commencer à s'épanouir.

        usage: [:]inscription|start
    """
    user_id = ctx.author.id

    if users.search(where('id') == user_id):
        await ctx.send(f"<@{user_id}> mais ? Toi déjà être inscris abruti...")
        return False

    users.insert({
        'type': 'users',
        'id': user_id,
        'challenge': None,
        'timestamp_start': None,
        'timestamp_end': None,
        'last_challenges': list(),
        'score': 0
    })
    await ctx.send(f"<@{user_id}> gooooooooooooooooo.")


@bot.command(aliases=['stop'])
async def desinscription(ctx):
    """
    👤 Mettre fin à son épanouissement.

        usage: [:]desinscription|stop
    """
    user_id = ctx.author.id

    if not users.search(where('id') == user_id):
        await ctx.send(f"<@{user_id}> mais ? Toi pas être inscris abruti...")
        return False

    users.remove(where('id') == user_id)
    await ctx.send(f"Aller bye bye <@{user_id}>.")


@bot.command(aliases=['a', 'add'])
async def ajout(ctx, challenge):
    """
    🃏 Ajoute un défi.

        usage: [:]ajout|a|add "défi"
    """
    # TODO empêcher l'ajout d'un défi si déjà enregistré avec de la recherche du sens de la phrase
    if challenges.search(where('description') == challenge):
        await ctx.send("HepHepHep il y est déjà ce défi boloss.")
        return False

    challenges.insert({
        'type': 'challenges',
        'author': ctx.author.id,
        'description': challenge
    })
    await ctx.send("Voila mon ptit pote le défi a été ajouté !")


@bot.command(aliases=['r', 'remove'])
async def retrait(ctx, challenge_id: int):
    """
    🃏 Supprime un défi.

        usage: [:]retrait|r|remove "défi id"
    """
    if not challenges.contains(doc_id=challenge_id):
        await ctx.send("T'es fou gadjo il existe po ton défi...")
        return False

    challenges.remove(doc_ids=[challenge_id])
    await ctx.send("Trop dur pour toi ce défi ? Le vla retiré.")


@bot.command(aliases=['i'])
async def info(ctx):
    """
    👤 Récupérer les informations joueur.

        usage: [:]info|i
    """
    # TODO afficher le défi de la personne mentionnée
    user_id = ctx.author.id

    Users = Query()
    db_user = users.get(Users.id == user_id)
    dc_user = await bot.fetch_user(user_id)
    user_name = dc_user.name

    if not db_user:
        await ctx.send(f"Eh oh pourquoi {user_name} tu ne joue pas ?")
        return False

    user_challenge_id = db_user['challenge']

    if user_challenge_id is None:
        await ctx.send(f"{user_name} tu n'a pas de défi.")
        return False

    user_challenge_description = challenges.all(
    )[user_challenge_id]['description']

    await ctx.send(f"{user_name} tu as pour challenge de `{user_challenge_description}`, bonne chance gros bg.")


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@bot.command(aliases=['c', 'challenges'])
async def defis(ctx, page_num: int = 0):
    """
    🃏 Lister les défis.

        usage: [:]defis|c|challenges <numero de page>
    """
    # inspiré de
    # https://stackoverflow.com/questions/61787520/i-want-to-make-a-multi-page-help-command-using-discord-py

    contents = [chunk for chunk in grouper(challenges, MAX_PER_PAGE)]
    last_page = len(contents) - 1
    cur_page = page_num - 1 if page_num > 0 and page_num - 1 <= last_page else 0

    async def page_embed(challenges, cur_page, last_page):
        count = cur_page * MAX_PER_PAGE
        embed = Embed(title='Liste des défis', color=BLURPLE)
        for challenge in challenges:
            if not challenge:
                continue
            dc_user = await bot.fetch_user(challenge['author'])
            embed.add_field(name=challenge['description'],
                            value=f"ID: {count}, Auteur: {dc_user.name}",
                            inline=True)
            count += 1
        embed.set_footer(text=f"Page {cur_page+1} sur {last_page+1}")
        return embed

    page = await page_embed(contents[cur_page], cur_page, last_page)
    message = await ctx.send(embed=page)
    # getting the message object for editing and reacting

    if last_page > 10:
        await message.add_reaction('⏮')
    if last_page > 5:
        await message.add_reaction('⏪')
    if last_page > 1:
        await message.add_reaction('◀️')
    if last_page > 1:
        await message.add_reaction('▶️')
    if last_page > 5:
        await message.add_reaction('⏩')
    if last_page > 10:
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
        except CommandInvokeError:
            await message.delete()
            break


@bot.command(aliases=['p', 'players'])
async def joueurs(ctx, page_num: int = 0):
    """
    👤 Lister les joueurs.

        usage: [:]joueurs|p|players <numero de page>
    """
    # inspiré de
    # https://stackoverflow.com/questions/61787520/i-want-to-make-a-multi-page-help-command-using-discord-py

    MAX_PER_PAGE = 9

    contents = [chunk for chunk in grouper(users, MAX_PER_PAGE)]
    last_page = len(contents) - 1
    cur_page = page_num - 1 if page_num > 0 and page_num - 1 <= last_page else 0

    async def page_embed(players, cur_page, last_page):
        count = cur_page * MAX_PER_PAGE
        embed = Embed(title='Liste des joueurs', color=BLURPLE)
        for player in players:
            if not player:
                continue
            dc_user = await bot.fetch_user(player['id'])
            embed.add_field(name=dc_user.name,
                            value=f"Challenge: {player['challenge']}, Score: {player['score']}",
                            inline=True)
            count += 1
        embed.set_footer(text=f"Page {cur_page+1} sur {last_page+1}")
        return embed

    page = await page_embed(contents[cur_page], cur_page, last_page)
    message = await ctx.send(embed=page)
    # getting the message object for editing and reacting

    if last_page > 10:
        await message.add_reaction('⏮')
    if last_page > 5:
        await message.add_reaction('⏪')
    if last_page > 1:
        await message.add_reaction('◀️')
    if last_page > 1:
        await message.add_reaction('▶️')
    if last_page > 5:
        await message.add_reaction('⏩')
    if last_page > 10:
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
        except CommandInvokeError:
            await message.delete()
            break


@bot.command(aliases=['g', 'get'])
async def defi(ctx):
    """
    🃏 Obtenir un défi.

        usage: [:]defi|g|get
    """
    user_id = ctx.author.id

    if users.get(where('id') == user_id)['challenge']:
        await ctx.send("Tu as déjà un défi champion.")
        return False

    # tirage du défi
    challenge_id = randint(0, len(challenges) - 1)
    challenge = challenges.all()[challenge_id]
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
                users.update(set('challenge', challenge_id), where('id') == user_id)
                users.update(set('timestamp', end.timestamp()), where('id') == user_id)

                # communication
                await message.edit(content=f"Défi accepté. \n<@{user_id}> tu vas devoir `{challenge_description}` du {challenge_start_date} au {challenge_end_date}.\nC'est irrévocable.")
                await message.remove_reaction(reaction, user)
                break

            elif str(reaction.emoji) == '👎':
                # perte de point
                users.update(add('score', REFUSE_POINT), where('id') == user_id)

                # communication
                await message.edit(content=f"Défi refusé.")
                await message.remove_reaction(reaction, user)
                break
        except CommandInvokeError:
            await message.delete()
            break


@bot.command()
async def evaluation(ctx):
    """
    🚧 WIP

        usage: [:]evaluation
    """
    user_id = ctx.author.id
    db_user = users.get(where('id') == user_id)
    user_challenge_id = db_user['challenge']
    user_challenge_name = challenges.all()[user_challenge_id]
    await ctx.send('Alors <@{user_id}> as tu réussi ton défi ?')
    await ctx.send('Pour rappel celui-ci était **{user_challenge_name}**')
    # get reaction or response
    pass


@bot.command(hidden=True)
async def poll(ctx, *, text):
    message = await ctx.send(text)
    for emoji in ('👍', '👎'):
        await message.add_reaction(emoji)

# TODO loop qui rappel les personnes ayant besoin de valider leur défi à ce jour

# TODO évaluation des defis
# TODO une durée aux défis ?
# TODO auteur != mentionné
# TODO listes de phrases

logger.info("Starting up and logging in...")
bot.run(DISCORD_TOKEN, bot=True)
logger.info("Completion timestamp")
logger.info("Done!")

from discord_slash.model import ContextMenuType
from discord_slash.context import MenuContext
from datetime import datetime, timedelta
from random import randint

from config import *
from utils import pagination, yes_no

import discord
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Bot
from discord_slash import SlashContext
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.context import ComponentContext
from tinydb import where
from tinydb.operations import add, set


@bot.event
async def on_ready():
    logger.info("Bot ready")


# WIP BUTTONS DEV

@slash.slash(name='ping')
async def _ping(ctx: SlashContext):
    await ctx.send(f"Pong! ({bot.latency*1000}ms)")


@slash.context_menu(target=ContextMenuType.MESSAGE,
                    name="commandname")
async def menuTest(ctx: MenuContext):
    await ctx.send(
        content=f"Responded! The content of the message targeted: {ctx.target_message.content}",
        hidden=True
    )

@bot.command(name='bouton')
async def bouton(ctx):
    buttons = [
        create_button(style=ButtonStyle.green, label="A green button"),
        create_button(style=ButtonStyle.red, label="A blue button")
    ]
    action_row = create_actionrow(*buttons)
    await ctx.send("bouton msg", components=[action_row])

    def check(button_ctx: ComponentContext):
        return button_ctx.author == ctx.author

    button_ctx: ComponentContext = await wait_for_component(bot, components=action_row, check=check)

    if button_ctx.component.get('style', '-1') == ButtonStyle.green:
        await button_ctx.edit_origin(content="You pressed the green button!", components=[])
    elif button_ctx.component.get('style', '-1') == ButtonStyle.red:
        await button_ctx.edit_origin(content="You pressed the red button!", components=[])


@bot.event
async def on_component(ctx: ComponentContext):
    # you may want to filter or change behaviour based on custom_id or message
    # await ctx.send(content=f"You selected {ctx.selected_options}")
    logger.info("Nothing")


@bot.command(name='selection')
async def selection(ctx):
    select = create_select(
        options=[  # the options in your dropdown
            create_select_option("Lab Coat", value="coat", emoji="🥼"),
            create_select_option("Test Tube", value="tube", emoji="🧪"),
            create_select_option("Petri Dish", value="dish", emoji="🧫"),
        ],
        # the placeholder text to show when no options have been chosen
        placeholder="Choose your option",
        min_values=1,  # the minimum number of options a user must select
        max_values=2,  # the maximum number of options a user can select
    )

    # like action row with buttons but without * in front of the variable
    await ctx.send("test", components=[create_actionrow(select)])


######################

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
    # TODO ajouter plusieurs défis simultanément (insert_multiple)
    challenge = ' '.join(args)

    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f"Wow {ctx.author.mention} fais attention ! Garde les défis secrets et ajoute les en DM bg.")
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
    user_id = ctx.author.id
    mentions = ctx.message.mentions or [ctx.author]

    embed = Embed(title='Info', color=ctx.author.colour)
    for mention in mentions:
        # db_user = db_users.get(Users.id == user_id)
        db_user = db_users.get(where('id') == mention.id)
        if not db_user:
            embed.add_field(name=mention.name,
                            value=f"Eh oh pourquoi tu ne joue pas ?",
                            inline=False)
            continue

        user_challenge_id = db_user['challenge']
        if user_challenge_id is None:
            embed.add_field(name=mention.name,
                            value=f"Aucun défi.",
                            inline=False)
            continue

        user_challenge_description = db_challenges.all()[
            user_challenge_id]['description']
        embed.add_field(name=mention.name,
                        value=f"`{user_challenge_description}`.",
                        inline=False)

    embed.set_footer(text=f"Bonne chance à tous les gros bg.")
    await ctx.send(embed=embed)


@bot.command(name='challenges', aliases=['lc', 'defis'])
async def list_challenges(ctx, page_num: int = 0):
    """
    🃏 Lister les défis.

        usage: [;]challenges|lc|defis <numero de page>
    """
    # TODO afficher que ceux de l'auteur dès la recherche
    # BUG Impossible de supprimer les réactions en MP

    if len(db_challenges) == 0:
        await ctx.send("Il serait peut-être temps d'enregistrer des défis...")
        return False

    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Je t'envoie ça en DM mi amor.")

    await pagination(ctx, 'CHALLENGES', 60, page_num)


@bot.command(name='players', aliases=['lp', 'joueurs'])
async def list_players(ctx, page_num: int = 0):
    """
    👤 Lister les joueurs.

        usage: [;]players|lp|joueurs <numero de page>
    """
    if len(db_users) == 0:
        await ctx.send("Il serait peut-être temps de commencer à jouer...")
        return False

    await pagination(ctx, 'USERS', 60, page_num)


@bot.command(name='get', aliases=['g', 'defi'])
async def get_challenge(ctx):
    """
    🃏 Obtenir un défi.

        usage: [;]get|g|defi
    """
    user_id = ctx.author.id

    # DM
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f"HHAHAHHAHAHAHHA. Non. Tu fais ça en public stp.")
        return False

    # Already challenged
    if db_users.get(where('id') == user_id)['challenge'] is not None:
        await ctx.send(f"Tu as déjà un défi champion.\nS'il est terminé va le valider avec `{DISCORD_PREFIX}evaluation`.")
        return False

    # No challenge
    if len(db_challenges) < 1:
        await ctx.send("Il n'y aucun défi dans la liste...")
        return False

    # Get challenge
    challenge_id = randint(0, len(db_challenges) - 1)
    challenge = db_challenges.all()[challenge_id]
    challenge_description = challenge['description']

    # Validation
    buttons = [
        create_button(style=ButtonStyle.green, label="Oui bien sur 8)"),
        create_button(style=ButtonStyle.red,
                      label="Non (-2 points si je suis si faible)")
    ]
    message = f"<@{user_id}> le defi `{challenge_description}` t'as été attribué es-tu partant(e) ?"
    action_row = create_actionrow(*buttons)
    await ctx.send(message, components=[action_row])

    answer, button_ctx = await yes_no(ctx, action_row)

    if answer:
        # Get dates
        start = datetime.now()
        end = start + timedelta(days=CHALLENGE_DELAY)
        challenge_start_date = start.strftime(DATE_FORMAT)
        challenge_end_date = end.strftime(DATE_FORMAT)

        # User update
        db_users.update(set('challenge', challenge_id), where('id') == user_id)
        db_users.update(set('timestamp_start', start.timestamp()),
                        where('id') == user_id)
        db_users.update(set('timestamp_end', end.timestamp()),
                        where('id') == user_id)

        # Communication
        await button_ctx.edit_origin(content=f"Défi accepté. \n<@{user_id}> tu vas devoir `{challenge_description}` du {challenge_start_date} au {challenge_end_date}.\nC'est irrévocable.", components=[])
    else:
        # Score update and Communication
        db_users.update(add('score', POINT_FOR_REFUSAL),
                        where('id') == user_id)
        await button_ctx.edit_origin(content=f"Défi refusé.", components=[])


@bot.command(name='validate', aliases=['v', 'valider'])
async def validate_challenge(ctx):
    """
    🃏 Terminer son défi.

        usage: [;]validate|v|valider
    """
    user_id = ctx.author.id
    db_user = db_users.get(where('id') == user_id)

    # Not a player
    if not db_user:
        await ctx.send(f"<@{user_id}> tu n'as pas démaré ta marche vers l'épanouissement.\nCommence avec `{DISCORD_PREFIX}inscription.`")

    # No challenge
    if db_user['challenge'] is None:
        await ctx.send(f"<@{user_id}> tu n'as pas encore de défi...")
        return False

    # Too early
    timestamp_end = datetime.fromtimestamp(db_user['timestamp_end'])
    if datetime.now().date() < timestamp_end.date():
        await ctx.send(f"Non non non, <@{user_id}> ton défi prendra fin le {timestamp_end.strftime(DATE_FORMAT)}")
        return False

    # Validation
    user_challenge_description = db_challenges.all(
    )[db_user['challenge']]['description']

    buttons = [
        create_button(style=ButtonStyle.green, label="Oui bien sur 8)"),
        create_button(style=ButtonStyle.red,
                      label="Non mais j'ai fais de mon mieux ! La prochaine fois j'y arriverais ouiiii")
    ]
    message = f"Alors <@{user_id}> as tu réussi ton défi ?\nPour rappel celui-ci était `{user_challenge_description}`."
    action_row = create_actionrow(*buttons)
    await ctx.send(message, components=[action_row])

    answer, button_ctx = await yes_no(ctx, action_row)

    # No answer
    if answer is None:
        return False

    # User update and Challenge removal
    db_users.update(set('challenge', None), where('id') == user_id)
    db_users.update(set('timestamp_start', None), where('id') == user_id)
    db_users.update(set('timestamp_end', None), where('id') == user_id)

    # Score update and Communication
    if answer:
        db_users.update(add('score', POINT_FOR_SUCCESS),
                        where('id') == user_id)
        await button_ctx.edit_origin(content=f"Bien joué <@{user_id}>, trop fort(e).", components=[])
    else:
        db_users.update(add('score', POINT_FOR_FAILURE),
                        where('id') == user_id)
        await button_ctx.edit_origin(content=f"Pas grave <@{user_id}>, tu feras mieux la prochaine fois ! :grimacing:", components=[])


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

reminder.start()

logger.info("Starting up and logging in...")
bot.run(DISCORD_TOKEN, bot=True)
logger.info("Completion timestamp")
logger.info("Done!")

from itertools import zip_longest

from config import *
from discord import Embed


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


async def page_embed_challenges(ctx, challenges, cur_page, last_page):
    count = cur_page * MAX_PER_PAGE
    embed = Embed(title='Liste des défis', color=BLURPLE)
    for challenge in challenges:
        if not challenge:
            continue

        dc_user = await ctx.bot.fetch_user(challenge['author'])

        embed.add_field(name=challenge['description'] if challenge['author'] == ctx.author.id else '-- SECRET --',
                        value=f"ID: {challenge.doc_id}, Auteur: {dc_user.name}",
                        inline=True)
        count += 1
    embed.set_footer(text=f"Page {cur_page+1} sur {last_page+1}")
    return embed


async def page_embed_users(ctx, players, cur_page, last_page):
    count = cur_page * MAX_PER_PAGE
    embed = Embed(title='Liste des joueurs', color=BLURPLE)
    for player in players:
        if not player:
            continue

        dc_user = await ctx.bot.fetch_user(player['id'])

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


async def pagination(ctx, subject, timeout=60, cur_page=0):
    # inspiré de https://stackoverflow.com/questions/61787520/i-want-to-make-a-multi-page-help-command-using-discord-py

    if subject is 'USERS':
        target = ctx
        iterable = db_users
        embed_process = page_embed_users
        reaction_remove_right = True
    elif subject is 'CHALLENGES':
        target = ctx.author
        iterable = db_challenges
        embed_process = page_embed_challenges
        reaction_remove_right = False
    else:
        logger.warning('Pagination for something that is not USERS or CHALLENGES')
        return False

    contents = [chunk for chunk in grouper(iterable, MAX_PER_PAGE)]
    last_page = len(contents) - 1
    cur_page = cur_page - 1 if cur_page > 0 and cur_page - 1 <= last_page else 0

    page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
    message = await target.send(embed=page)
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

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            # waiting for a reaction to be added - times out after x seconds, 60 in this

            if str(reaction.emoji) == '▶️' and cur_page != last_page:
                cur_page += 1
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '◀️' and cur_page >= 1:
                cur_page -= 1
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏩' and cur_page <= last_page - 5:
                cur_page += 5
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏪' and cur_page >= 5:
                cur_page -= 5
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏭' and cur_page <= last_page - 10:
                cur_page += 10
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '⏮' and cur_page >= 10:
                cur_page -= 10
                page = await embed_process(ctx, contents[cur_page], cur_page, last_page)
                await message.edit(embed=page)
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)

            else:
                if reaction_remove_right:
                    await message.remove_reaction(reaction, user)
        except Exception as err:
            logger.error(err)
            logger.warning('Timeout maybe (pagination)')
            await message.delete()
            break


async def yes_no(ctx, message):
    await message.add_reaction('👍')
    await message.add_reaction('👎')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)

            if str(reaction.emoji) == '👍':
                return True

            elif str(reaction.emoji) == '👎':
                return False
        except Exception as err:
            logger.warning('Timeout maybe (evaluation)')
            return None
    return None

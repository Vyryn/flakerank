import random
import datetime
from typing import Optional

import aiohttp
import hikari
import tanjun
import yuyo
from tanjun.abc import SlashContext

from utils.config import Config


def url_from_wts(wts: list[int]) -> str:
    total_wt = sum(wts)
    mul_altitude = wts[5] / total_wt  # 0.1
    mul_spin = wts[4] / total_wt  # 0.1
    mul_velocity = wts[3] / total_wt  # 0.15
    mul_purity = wts[2] / total_wt  # 0.15
    mul_power = wts[1] / total_wt  # 0.25
    mul_faction = wts[0] / total_wt  # 0.25
    # Construct url
    url = f"{Config.s.FLAKE_ENDPOINT}?" \
          f"mul_altitude={mul_altitude}&" \
          f"mul_spin={mul_spin}&" \
          f"mul_velocity={mul_velocity}&" \
          f"mul_purity={mul_purity}&" \
          f"mul_power={mul_power}&" \
          f"mul_faction={mul_faction}"
    return url


def fac_to_color(faction: str) -> int:
    if faction == "tri":
        return hikari.colors.Color(0x0000FF)
    elif faction == "quad":
        return hikari.colors.Color(0xFF0000)
    elif faction == "penta":
        return hikari.colors.Color(0x800080)
    elif faction == "hexa":
        return hikari.colors.Color(0xFFD700)
    else:
        return hikari.colors.Color(0x808080)


def embed_page(item: dict, wts: list[int]) -> hikari.Embed:
    embed = hikari.Embed(title=str(item['name']).title(),
                         description=f"Result #{item['id'] + 1} for {wts}:",
                         url=item["uri"],
                         color=fac_to_color(str(item["faction"]).title()),
                         timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.set_image(item["image"])
    embed.add_field("Faction", f'{item["faction"]}', inline=True)
    embed.add_field("Power", f'{item["power"]} ({round(item["perc_power"] * 100, 1)}th percentile)', inline=True)
    embed.add_field("Purity", f'{item["purity"]} ({round(item["perc_purity"] * 100, 1)}th percentile)', inline=True)
    embed.add_field("Velocity", f'{item["velocity"]} ({round(item["perc_velocity"] * 100, 1)}th percentile)',
                    inline=True)
    embed.add_field("Spin", f'{item["spin"]} ({round(item["perc_spin"] * 100, 1)}th percentile)', inline=True)
    embed.add_field("Altitude", f'{item["altitude"]} ({round(item["perc_altitude"] * 100, 1)}th percentile)',
                    inline=True)
    if item["for_sale"] > 0:
        embed.add_field("Sale", f"This fractal is on sale for {item['price_sol']} SOL on "
                                f"{str(item['marketplace']).title()}.")
    embed.set_footer(text=f"Owner: {item['owner']}")
    return embed


async def unlim_fractal_iterator(url, wts):
    page = 1
    while True:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            resp = await session.get(f'{url}&page={page}')
            result = await resp.json()
        data = result["data"]
        for item in data:
            yield hikari.UNDEFINED, embed_page(item, wts)
        page += 1


async def search_fractal(name):
    page = 1
    while True:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            resp = await session.get(f"{Config.s.FLAKE_ENDPOINT}?s={name}&page={page}")
            result = await resp.json()
            data = result["data"]
            for item in data:
                yield hikari.UNDEFINED, embed_page(item, name)
        page += 1


fractals = tanjun.Component()

group = fractals.with_slash_command(tanjun.slash_command_group("fractals", "Get info on fractals.",
                                                               default_to_ephemeral=False))


@group.with_command
@tanjun.with_int_slash_option("faction_wt", "The weighting to give to faction. 1 if unspecified.")
@tanjun.with_int_slash_option("power_wt", "The weighting to give to power. 1 if unspecified.")
@tanjun.with_int_slash_option("purity_wt", "The weighting to give to purity. 1 if unspecified.")
@tanjun.with_int_slash_option("velocity_wt", "The weighting to give to velocity. 1 if unspecified.")
@tanjun.with_int_slash_option("spin_wt", "The weighting to give to spin. 1 if unspecified.")
@tanjun.with_int_slash_option("altitude_wt", "The weighting to give to altitude. 1 if unspecified.")
@tanjun.as_slash_command("browse", "Search for fractals based on the stats that matter most to you. Higher "
                                   "weighting = more important.")
async def fractal_browse_command(ctx: SlashContext,
                                 bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBot),
                                 client: tanjun.Client = tanjun.injected(type=tanjun.Client),
                                 component_client: yuyo.ComponentClient = tanjun.injected(type=yuyo.ComponentClient),
                                 faction_wt: Optional[int] = 1,
                                 power_wt: Optional[int] = 1,
                                 purity_wt: Optional[int] = 1,
                                 velocity_wt: Optional[int] = 1,
                                 spin_wt: Optional[int] = 1,
                                 altitude_wt: Optional[int] = 1) -> None:
    # Generate uid for this invocation's specific button ids
    uid = random.randrange(10 ** 9, 10 ** 10 - 1)
    # Transform into fractions
    wts = [faction_wt, power_wt, purity_wt, velocity_wt, spin_wt, altitude_wt]
    url = url_from_wts(wts)

    paginator = yuyo.ComponentPaginator(unlim_fractal_iterator(url, wts),
                                        authors=(ctx.author,),
                                        timeout=datetime.timedelta(minutes=10))
    if first_response := await paginator.get_next_entry():
        content, embed = first_response
        message = await ctx.respond(content=content, component=paginator, embed=embed, ensure_result=True)
        component_client.set_executor(message, paginator)
        return
    await ctx.respond("Entry not found")


@group.with_command
@tanjun.with_str_slash_option("name", "The fractal name to search for.")
@tanjun.as_slash_command("search", "Search for fractals by name.")
async def fractal_search_command(ctx: SlashContext,
                                 name: str,
                                 bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBot),
                                 client: tanjun.Client = tanjun.injected(type=tanjun.Client),
                                 component_client: yuyo.ComponentClient = tanjun.injected(type=yuyo.ComponentClient),
                                 ):
    paginator = yuyo.ComponentPaginator(search_fractal(name),
                                        authors=(ctx.author,),
                                        timeout=datetime.timedelta(minutes=10))
    if first_response := await paginator.get_next_entry():
        content, embed = first_response
        message = await ctx.respond(content=content, component=paginator, embed=embed, ensure_result=True)
        component_client.set_executor(message, paginator)
        return
    await ctx.respond("Entry not found")


@group.with_command
@tanjun.as_slash_command("help", "Helpful information. Start here.")
async def fractal_help_command(ctx: SlashContext):
    content = 'Welcome to FlakeRank!\n' \
              'To search for fractals by name, you can type `/fractals search name`\n\n' \
              'To find fractals with the specific stats you value most, you can use the `/fractals browse` command.\n' \
              'This command lets you specify how much each stat matters to you.\n\n' \
              '`/fractals browse` with every weight equal would search for the most impressive fractals with ' \
              'each stat mattering equally, whether they are set to 1 or 100.\n\n' \
              '`/fractals browse altitude_wt:10 spin_wt:1 velocity_wt:1 purity_wt:5 power_wt:1 faction_wt:0` would ' \
              'search for fractals mostly by altitude, indicating altitude matters to you twice as much as purity' \
              ' and ten times as much as spin, power, or velocity. It also indicates you do not care about faction ' \
              'at all.\n\n' \
              'If you prefer, you can use good old percentages exactly the same way:\n' \
              '`/fractals browse altitude_wt:10 spin_wt:10 velocity_wt:15 purity_wt:15 power_wt:25 faction_wt:25` ' \
              'cares 10% about altitude, 10% about spin, 15% about velocity, 15% about purity, 25% about power ' \
              'and 25% about faction.\n\n' \
              'Mix and match to your heart\'s content: Ultimately you define the perfect ' \
              'fractal for you.\n' \
              '(That said, this ability to fine tune what you care about could be very useful for finding' \
              ' overlooked fractals for specific niche uses in future games...)'
    await ctx.create_initial_response(content=content, ephemeral=True)


load_slash = fractals.make_loader()

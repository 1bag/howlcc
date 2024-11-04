import discord
from discord.ext import commands
from discord.ui import Select, View
import os
import json
import requests
import random
import asyncio

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
ADMIN_CHANNEL_ID = 1301541083687157866
AUTHORIZED_USERS = {
    1095069376983613623, 
    1164595038064496863, 
    1033671521283084358, 
    1088497016147025951
}

DEFAULT_PREFIX = "!"
prefixes = {}

def load_prefix():
    if os.path.exists('prefix.json'):
        with open('prefix.json', 'r') as f:
            return json.load(f)
    return {}

def save_prefix(prefix_data):
    with open('prefix.json', 'w') as f:
        json.dump(prefix_data, f, indent=4)

prefixes = load_prefix()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

def get_prefix(bot, message):
    return prefixes.get(str(message.guild.id), DEFAULT_PREFIX)

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

def load_boost_history():
    if os.path.exists('boosts.json'):
        with open('boosts.json', 'r') as f:
            return json.load(f)
    return {}

def save_boost_history(boost_history):
    with open('boosts.json', 'w') as f:
        json.dump(boost_history, f, indent=4)

boost_history = load_boost_history()

default_stream_name = ".gg/howlcc"
default_stream_url = "https://www.youtube.com/watch?v=TCs_DZkkijI"
stream_image_url = "https://images-ext-1.discordapp.net/external/kZIvX7K_nPY4X7-e1JacCmx-VHtAT3D8m6ra4sQDxXg/%3Fsize%3D1024/https/cdn.discordapp.com/icons/1283571069491609610/a_19f69c46e03b339755d8b726516f91e9.gif?width=473&height=473"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    streaming_activity = discord.Streaming(name=default_stream_name, url=default_stream_url)
    await bot.change_presence(activity=streaming_activity)
    await update_boost_history()

class StatusSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Online", value="online"),
            discord.SelectOption(label="Do Not Disturb", value="dnd"),
            discord.SelectOption(label="Idle", value="idle"),
        ]
        super().__init__(placeholder="Select a status...", options=options)

    async def callback(self, interaction: discord.Interaction):
        status_mapping = {
            "online": discord.Status.online,
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
        }
        selected_status = self.values[0]
        new_status = status_mapping[selected_status]
        await bot.change_presence(status=new_status)
        await interaction.response.send_message(f"Bot status changed to **{selected_status.capitalize()}**!", ephemeral=True)

@bot.command()
async def botstatus(ctx):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))
    view = View()
    view.add_item(StatusSelect())
    await ctx.send(content="Select the bot's status:", view=view)

@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title="Member Joined",
        description=f"{member.mention} has joined the server!",
        color=0xff8500
    )
    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    embed = discord.Embed(
        title="Member Left",
        description=f"{member.mention} has left the server.",
        color=0xff8500
    )
    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        boost_history[str(after.id)] = str(after.name)
        save_boost_history(boost_history)
        embed = discord.Embed(
            title="Boosted Server",
            description=f"{after.mention} has boosted the server!",
            color=0xff8500
        )
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            await admin_channel.send(embed=embed)

    elif before.premium_since is not None and after.premium_since is None:
        if str(before.id) in boost_history:
            del boost_history[str(before.id)]
            save_boost_history(boost_history)
            embed = discord.Embed(
                title="Boost Expired",
                description=f"{before.mention} has unboosted the server.",
                color=0xff8500
            )
            admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                await admin_channel.send(embed=embed)

async def update_boost_history():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("The bot is not in the specified guild.")
        return

    booster_role = guild.get_role(1301549280145834050)
    if booster_role:
        for member in booster_role.members:
            boost_history[str(member.id)] = str(member.name)

    save_boost_history(boost_history)

@bot.command()
async def tos(ctx):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    embed = discord.Embed(
        title="**Howl Rules | Guidelines**",
        description=(
            "**Advertisement & Promotion:** Not allowed without permission (24-48 Hour Mute)\n\n"
            "**DM Advertising:** Not allowed, leads to kick/permanent ban\n\n"
            "**Flooding & Spamming:** Not allowed (24 Hour Mute)\n\n"
            "**NSFW:** Not allowed (4 Week Mute - Permanent Ban)\n\n"
            "**Doxxing:** Not allowed (Permanent Ban)\n\n"
            "**Scamming:** Not allowed (Permanent Ban)\n\n"
            "**CP/CSEM:** Not allowed (4 Week Mute - Permanent Ban)\n\n"
            "**Death Threats:** Not allowed (Up to Server Manager)\n\n"
            "**Suggestive Jokes:** Not allowed (4 Week Mute - Permanent Ban)\n\n"
            "**Spamming DMs:** Not allowed (Permanent Ban)\n\n"
            "**Discord TOS:** Follow Discord's TOS and Guidelines: https://discord.com/terms | https://discord.com/guidelines"
        ),
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    compliance_issues = await check_server_status()
    if not compliance_issues:
        description = "✅ The server is following the Discord Terms of Service."
    else:
        description = "❌ The server has the following compliance issues:\n" + "\n".join(compliance_issues)

    embed = discord.Embed(
        title="Server Compliance Status",
        description=description,
        color=0xff8500
    )
    await ctx.send(embed=embed)

async def check_server_status():
    compliance_issues = []
    if len(compliance_issues) == 0:
        compliance_issues.append("Everything seems fine!")
    return compliance_issues

@bot.command()
async def boost(ctx):
    if ctx.guild is None:
        return await ctx.send(embed=discord.Embed(title="Error", description="This command can only be used in a server.", color=0xff8500))

    boost_list = [f"<@{member_id}> - {username}" for member_id, username in boost_history.items()]
    if boost_list:
        boost_description = "\n".join(boost_list)
        embed = discord.Embed(
            title="Boost List",
            description=f"The following users have boosted the server:\n{boost_description}",
            color=0xff8500
        )
    else:
        embed = discord.Embed(
            title="Boost List",
            description="No users have boosted the server.",
            color=0xff8500
        )

    await ctx.send(embed=embed)

@bot.command()
async def setstream(ctx, *, stream_info: str):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    try:
        stream_name, stream_url = stream_info.split(' ', 1)
    except ValueError:
        return await ctx.send(embed=discord.Embed(title="Error", description="Please provide both a stream name and a stream URL separated by a space.", color=0xff0000))

    streaming_activity = discord.Streaming(name=stream_name, url=stream_url)
    await bot.change_presence(activity=streaming_activity)

    embed = discord.Embed(
        title="Streaming Status Updated",
        description=f"The bot is now streaming: **{stream_name}**\nWatch at: {stream_url}",
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def streamimage(ctx):
    embed = discord.Embed(
        title="Current Stream Image",
        description="Here's the image associated with the current stream:",
        color=0xff8500
    )
    embed.set_image(url=stream_image_url)
    await ctx.send(embed=embed)

@bot.command()
async def whitelist_list(ctx):
    role_id = 1301549273959104594
    role = ctx.guild.get_role(role_id)

    if role is None:
        return await ctx.send(embed=discord.Embed(title="Error", description="The specified role could not be found.", color=0xff0000))

    members_with_role = role.members
    if members_with_role:
        member_list = [f"<@{member.id}> - {member.display_name}" for member in members_with_role]
        member_list_str = "\n".join(member_list)
        embed = discord.Embed(
            title=f"Members with the whitelist role: {role.name}",
            description=member_list_str,
            color=0xff8500
        )
    else:
        embed = discord.Embed(
            title=f"Members with the whitelist role: {role.name}",
            description="No members have this role.",
            color=0xff8500
        )

    await ctx.send(embed=embed)

@bot.command()
async def whitelist(ctx, member: discord.Member):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    role_id = 1301549273959104594
    role = ctx.guild.get_role(role_id)

    if role is None:
        return await ctx.send(embed=discord.Embed(title="Error", description="The specified role could not be found.", color=0xff0000))

    try:
        await member.add_roles(role)
        await ctx.send(embed=discord.Embed(title="Whitelist Update", description=f"{member.mention} has been added to the whitelist role {role.name}.", color=0xff8500))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(title="Error", description="I do not have permission to add roles.", color=0xff0000))
    except discord.HTTPException:
        await ctx.send(embed=discord.Embed(title="Error", description="Failed to add role. Please try again.", color=0xff0000))

@bot.command()
async def blacklist(ctx, member: discord.Member):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    role_id = 1301549273959104594
    role = ctx.guild.get_role(role_id)

    if role is None:
        return await ctx.send(embed=discord.Embed(title="Error", description="The specified role could not be found.", color=0xff0000))

    try:
        await member.remove_roles(role)
        await ctx.send(embed=discord.Embed(title="Blacklist Update", description=f"{member.mention} has been removed from the whitelist role {role.name}.", color=0xff8500))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(title="Error", description="I do not have permission to remove roles.", color=0xff0000))
    except discord.HTTPException:
        await ctx.send(embed=discord.Embed(title="Error", description="Failed to remove role. Please try again.", color=0xff0000))

@bot.command()
async def prices(ctx):
    embed = discord.Embed(
        title="**Howl Script Pricing**",
        description=(
            "Newcomer `->` $20\n"
            "HowlV2 Buyer `->` $15\n"
            "Robux `->` 1,700\n"
            "HowlV2 Buyer Robux `->` 1,400\n"
            "Create a ticket here `->` https://discord.com/channels/1283571069491609610/1301549921941458945"
        ),
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx, command_name: str):
    command_info = {
        "tos": "The `!tos` command shows the Terms of Service and rules of the server.",
        "boost": "The `!boost` command displays the list of users who have boosted the server.",
        "whitelist_list": "The `!whitelist_list` command lists members with the whitelist role.",
        "whitelist": "The `!whitelist @user` command adds a user to the whitelist role.",
        "blacklist": "The `!blacklist @user` command removes a user from the whitelist role.",
        "prices": "The `!prices` command shows the pricing for Howl scripts and associated items.",
        "ping": "The `!ping` command returns the bot's current latency.",
        "userinfo": "The `!userinfo @member` command displays information about the specified user.",
        "serverinfo": "The `!serverinfo` command displays information about the server.",
        "prefix": "The `!prefix <new_prefix>` command allows you to change the command prefix for the bot.",
        "status": "The `!status` command checks if the server is following the Terms of Service.",
        "avatar": "The `!avatar @user` command displays the avatar of the specified user.",
        "poll": "The `!poll <question>` command creates a poll with the specified question.",
        "usercount": "The `!usercount` command displays the current number of members in the server.",
        "roles": "The `!roles` command lists all roles in the server and their member counts.",
        "emojis": "The `!emojis` command displays a list of all custom emojis in the server.",
        "streamimage": "The `!streamimage` command shows the image associated with the current stream.",
        "setstream": "The `!setstream <stream_name> <stream_url>` command sets the streaming status for the bot.",
        "clear": "The `!clear <number>` command deletes the specified number of messages from the channel.",
        "suggest": "The `!suggest <your_suggestion>` command submits a suggestion for the bot or server.",
        "quote": "The `!quote` command returns a random inspirational quote.",
        "servericon": "The `!servericon` command displays the server's icon.",
        "banner": "The `!banner @user` command displays the specified user's banner.",
        "crypto": "The `!crypto <currency>` command retrieves the price of the specified cryptocurrency.",
        "roll": "The `!roll <number>` command simulates rolling a die with the specified number of sides.",
        "flip": "The `!flip` command simulates flipping a coin.",
        "fact": "The `!fact` command returns a random interesting fact.",
        "timer": "The `!timer <seconds>` command sets a timer for the specified number of seconds."
    }

    command_name = command_name.lower()
    info_message = command_info.get(command_name, "Command not found.")
    embed = discord.Embed(
        title=f"Information about `{command_name}`",
        description=info_message,
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Pong",
        description=f"Latency: {latency} ms",
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"User Info for {member.display_name}",
        color=0xff8500
    )
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Joined Server On", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Account Created On", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "No roles", inline=False)
    embed.add_field(name="Status", value=str(member.status).title(), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"Server Info for {guild.name}",
        color=0xff8500
    )
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=False)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Role Count", value=len(guild.roles), inline=False)
    region = str(guild.region) if hasattr(guild, 'region') else "N/A"
    embed.add_field(name="Region", value=region, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def prefix(ctx, new_prefix: str):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    prefixes[str(ctx.guild.id)] = new_prefix
    save_prefix(prefixes)

    embed = discord.Embed(
        title="Prefix Change",
        description=f"The command prefix has been changed to `{new_prefix}`.",
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def authorized(ctx):
    if ctx.author.id not in AUTHORIZED_USERS:
        return await ctx.send(embed=discord.Embed(title="Unauthorized", description="You are not authorized to use this command.", color=0xff8500))

    authorized_mentions = [f"<@{user_id}>" for user_id in AUTHORIZED_USERS]
    if authorized_mentions:
        embed = discord.Embed(
            title="Authorized Users",
            description="The following users are authorized to use certain commands:\n" + "\n".join(authorized_mentions),
            color=0xff8500
        )
    else:
        embed = discord.Embed(
            title="Authorized Users",
            description="There are currently no authorized users.",
            color=0xff8500
        )

    await ctx.send(embed=embed)

@bot.command()
async def emojis(ctx):
    emojis = ctx.guild.emojis
    if emojis:
        emoji_list = " ".join(str(emoji) for emoji in emojis)
        embed = discord.Embed(title="Custom Emojis", description=emoji_list, color=0xff8500)
    else:
        embed = discord.Embed(title="Custom Emojis", description="No custom emojis found in this server.", color=0xff8500)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        return await ctx.send(embed=discord.Embed(title="Error", description="You need to specify a number greater than 0!", color=0xff0000))

    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(embed=discord.Embed(title="Clear Messages", description=f"Deleted {len(deleted) - 1} messages.", color=0x00ff00), delete_after=5)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"{member}'s Avatar", color=0xff8500)
    embed.set_image(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, *, question: str):
    message = await ctx.send(embed=discord.Embed(title="Poll", description=f"Poll: {question}\nReact with 👍 or 👎 to vote!", color=0xff8500))
    await message.add_reaction("👍")
    await message.add_reaction("👎")

@bot.command()
async def usercount(ctx):
    member_count = ctx.guild.member_count
    embed = discord.Embed(
        title="Current Member Count",
        description=f"The server currently has **{member_count}** members.",
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def roles(ctx):
    roles_list = [f"{role.name}: {len(role.members)} members" for role in ctx.guild.roles]
    roles_description = "\n".join(roles_list) if roles_list else "No roles found."
    embed = discord.Embed(
        title=f"Roles in {ctx.guild.name}",
        description=roles_description,
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def weather(ctx, *, location: str):
    api_key = os.getenv('WEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        embed = discord.Embed(
            title=f"Weather in {location.capitalize()}",
            description=f"Condition: {description}\nTemperature: {temp}°C",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=discord.Embed(title="Error", description="Location not found.", color=0xff0000))

@bot.command()
async def suggest(ctx, *, suggestion: str):
    suggestion_channel_id = 123456789012345678
    suggestion_channel = bot.get_channel(suggestion_channel_id)

    if suggestion_channel:
        await suggestion_channel.send(f"New Suggestion: {suggestion} - Suggested by {ctx.author.mention}")
        await ctx.send(embed=discord.Embed(title="Suggestion Submitted", description="Thank you for your suggestion!", color=0xff8500))
    else:
        await ctx.send(embed=discord.Embed(title="Error", description="Suggestion channel not found.", color=0xff0000))

@bot.command()
async def quote(ctx):
    quotes = [
        "The best way to predict the future is to create it.",
        "You only live once, but if you do it right, once is enough.",
        "Act as if what you do makes a difference. It does.",
        "Success is not the key to happiness. Happiness is the key to success.",
        "You miss 100% of the shots you don't take."
    ]
    embed = discord.Embed(
        title="Random Quote",
        description=random.choice(quotes),
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def servericon(ctx):
    embed = discord.Embed(
        title="Server Icon",
        color=0xff8500
    )
    embed.set_image(url=ctx.guild.icon.url if ctx.guild.icon else "No icon available.")
    await ctx.send(embed=embed)

@bot.command()
async def banner(ctx, member: discord.Member):
    if member.banner is None:
        return await ctx.send(embed=discord.Embed(title="Error", description=f"{member.mention} does not have a banner.", color=0xff0000))

    embed = discord.Embed(
        title=f"{member.display_name}'s Banner",
        color=0xff8500
    )
    embed.set_image(url=member.banner.url)
    await ctx.send(embed=embed)

@bot.command()
async def crypto(ctx, currency: str):
    api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={currency}&vs_currencies=usd"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if currency in data:
            price = data[currency]['usd']
            embed = discord.Embed(
                title=f"{currency.capitalize()} Price",
                description=f"The current price of {currency.capitalize()} is ${price} USD.",
                color=0xff8500
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(title="Error", description="Cryptocurrency not found.", color=0xff0000))
    else:
        await ctx.send(embed=discord.Embed(title="Error", description="Failed to retrieve data. Please try again later.", color=0xff0000))

@bot.command()
async def roll(ctx, sides: int = 6):
    if sides <= 0:
        await ctx.send(embed=discord.Embed(title="Error", description="You must roll a die with at least 1 side.", color=0xff0000))
    else:
        result = random.randint(1, sides)
        await ctx.send(embed=discord.Embed(title="Die Roll", description=f"You rolled a {result} on a {sides}-sided die.", color=0xff8500))

@bot.command()
async def flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=discord.Embed(title="Coin Flip", description=f"The result is: **{result}**", color=0xff8500))

@bot.command()
async def fact(ctx):
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3000 years old and still edible.",
        "Octopuses have three hearts and blue blood.",
        "Bananas are berries, but strawberries aren't.",
        "A group of flamingos is called a 'flamboyance'.",
        "There is a species of jellyfish that is immortal."
    ]
    embed = discord.Embed(
        title="Interesting Fact",
        description=random.choice(facts),
        color=0xff8500
    )
    await ctx.send(embed=embed)

@bot.command()
async def timer(ctx, seconds: int):
    if seconds <= 0:
        await ctx.send(embed=discord.Embed(title="Error", description="Please specify a positive number.", color=0xff0000))
        return

    await ctx.send(embed=discord.Embed(title="Timer Set", description=f"Timer for **{seconds} seconds** started!", color=0xff8500))
    await asyncio.sleep(seconds)
    await ctx.send(embed=discord.Embed(title="Time's Up!", description="⏰ The timer has elapsed!", color=0xff8500))

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="User Banned", description=f"{member.mention} has been banned from the server!", color=0xff8500)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title="User Kicked", description=f"{member.mention} has been kicked from the server!", color=0xff8500)
    await ctx.send(embed=embed)

bot.run(TOKEN)

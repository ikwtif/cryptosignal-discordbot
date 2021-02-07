import tornado.web
import json
import asyncio
import re
from jinja2 import Template
from pprint import pprint
from conf import Configuration
import discord
from discord.ext import commands
from datetime import datetime
import platform
import sys
import tornado.web
import aiodocker
import discord
from discord.ext import commands
import logging

# TODO - fix docker setup

# # monkey patch du to 3.8 breaking change for tornado
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# {
# loading config
def config():
    conf = Configuration()
    settings = conf.settings
    discordbot = conf.discordbot
    message_templater = conf.message
    dockerimage = conf.docker
    return settings, discordbot, message_templater, dockerimage


settings, discordbot, message_templater, dockerimage = config()
# }

# logging setup
loglevel = settings.get('loglevel')
if loglevel:
    if loglevel == 'info':
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    elif loglevel == 'debug':
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)

# {
# bot setup
bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    logging.info("the bot is ready")

@bot.command()
async def clear(ctx, amount=100):
    await ctx.channel.purge(limit=amount)

@bot.command()
async def test(ctx):
    await ctx.send("it works")

async def clear_messages(amount=100):
    # TODO not used
    chnls = list()
    for channel in discordbot['channels'].keys():
        if channel == 'channel_main':
            pass
        elif not (discordbot['channels'][channel]['id'] in chnls):
            chnls.append(discordbot['channels'][channel]['id'])
    for channel in chnls:
        channelid = bot.get_channel(int(channel))
        messages = await channelid.history().flatten()
        logging.info(f'deleting messages in channel: {channel}')
        await channelid.delete_messages(messages)
# }


def _find_number(prices, text):
    # TODO not used
    f = re.search(text, prices)
    return f.group(1)


def _title_message_templater(data):
    message_template = Template(message_templater['title_template'])
    new_title = str()
    new_title += message_template.render(**data)
    return new_title


def save_content(messages):
    # Do not use while running inside docker container
    filename = messages[0]['market']
    with open(f'{filename}.txt', 'w+') as out:
        out.write(messages)
        logging.info(f'printing message recieved and saved in {filename}.txt')

def _title_indicator_message_templater(data):
    message_template = Template(message_templater['title_indicator_template'])
    new_message = str()
    new_message += message_template.render(**data)
    return new_message

def _indicator_message_templater(data):
    message_template = Template(message_templater['indicator_template'])
    new_message = str()
    new_message += message_template.render(**data)
    return new_message


def title_data(messages):
    candle_period = 'NA'
    price_high = 'NA'
    price_low = 'NA'
    price_close = 'NA'

    indicator_analyses = messages[0].get('analysis')
    if indicator_analyses:
        indicator_config = indicator_analyses.get('config')
        if indicator_config:
            candle_period = str(indicator_config.get('candle_period', 'NA'))

    price_value = messages[0].get('price_value')
    if price_value:
        price_high = price_value.get('high', 'NA')
        price_low = price_value.get('low', 'NA')
        price_close = price_value.get('close', 'NA')

    title = {
            'base_currency': messages[0].get('base_currency', 'NA'),
            'quote_currency': messages[0].get('quote_currency', 'NA'),
            'candle_period': candle_period,
            'market': messages[0].get('market', 'NA'),
            'date': messages[0].get('creation_date', 'NA'),
            'exchange': messages[0].get('exchange', 'NA'),
            'prices': messages[0].get('prices', 'NA'),
            'price_high': price_high,
            'price_low': price_low,
            'price_close': price_close
    }
    logging.debug(f'title data \n {title}')
    return title


def indicator_data(indicator):
    candle_period = 'NA'
    period_count = 'NA'
    indicator_analyses = indicator.get('analysis')
    if indicator_analyses:
        indicator_config = indicator_analyses.get('config')
        if indicator_config:
            candle_period = str(indicator_config.get('candle_period', 'NA'))
            period_count = str(indicator_config.get('period_count', 'NA'))

    indicator = {
        'hot_label': indicator.get('hot_label', 'NA'),
        'cold_label': indicator.get('hot_label', 'NA'),
        'indicator_label': indicator.get('indicator_label', 'NA'),
        'hot_cold_label': indicator.get('hot_cold_label', 'NA'),
        'status': indicator.get('status', 'NA'),
        'last_status': indicator.get('last_status', 'NA'),
        'values': indicator.get('values', 'NA'),
        'candle_period': candle_period,
        'period_count': period_count
    }
    logging.debug(f'indicator data \n {indicator}')
    return indicator


def config_find(to_find, to_check, channel=None):
    if channel is None:
        channel = '< undefined >'
    found = False
    if to_check:
        logging.info(f'Searching {to_find} in {to_check} for channel {channel}')
        if isinstance(to_check, str):
            if to_check == 'all':
                logging.info(f'Found channel for: {to_find} in {channel} -- {to_check}')
                found = True
            elif to_find == to_check:
                logging.info(f'Found channel for: {to_find} in {channel} -- {to_check}')
                found = True
        elif isinstance(to_check, list):
            if to_find in to_check:
                logging.info(f'Found channel for: {to_find} in {channel} -- {to_check}')
                found = True
    return found


async def parse_message(messages, fh):
    logging.debug(f'message recieved: \n {messages}')
    if settings.get('debug') is True:
        save_content(messages)
    msg_candle_period = messages[0].get('analysis').get('config').get('candle_period')
    msg_token = messages[0].get('base_currency')
    msg_quote = messages[0].get('quote_currency')
    logging.info(f'parsing message for {msg_token, msg_candle_period}')

    # {
    # creating list of discord channels based on config
    channels = list()
    channels_discord = discordbot.get('channels')
    logging.debug(f'Setup for channels: {channels_discord}')
    if channels_discord:
        for chan in channels_discord.keys():
            chnl_tokens = channels_discord[chan].get('base_currency')
            channel_candle_period = channels_discord[chan].get('candle_period')
            channel_quote = channels_discord[chan].get('quote_currency')
            find_cnl_token = config_find(to_check=chnl_tokens, to_find=msg_token, channel=chan)
            find_chnl_candle = config_find(to_check=channel_candle_period, to_find=msg_candle_period, channel=chan)
            find_chnl_quote = config_find(to_check=channel_quote, to_find=msg_quote, channel=chan)
            if find_cnl_token and find_chnl_candle and find_chnl_quote:
                channels.append(channels_discord[chan])
                logging.info(f'Adding channel {chan} to messages list for {msg_token}/{msg_quote}, {msg_candle_period}')
    if len(channels) == 0:
        not_found = discordbot.get('channel_notfound')
        if not_found:
            channels.append(not_found)
            logging.info(f'Using channel <not found> for {msg_token}')
    # }

    # {
    # Preparing messages
    discord_messages = list()
    for channel in channels:
        logging.info(f'preparing message for channel {channel}')
        data_title = title_data(messages)
        indicator = channel.get('indicator')
        title = _title_message_templater(data_title)
        to_send = discord.Embed(title=title,
                                type="rich")
        if channel.get('title'):
            for data in messages:
                signal = data['indicator']
                logging.info(f'matching {signal} with channel indicator {indicator}')
                if signal == indicator:
                    data_indicator = indicator_data(messages[0])
                    data_total = {**data_title, **data_indicator}
                    title = _title_indicator_message_templater(data_total)
                    to_send = discord.Embed(title=title,
                                            type="rich")
                    discord_messages.append((channel, to_send))
                    break
        else:
            for data in messages:
                signal = data['indicator']
                use = config_find(to_check=indicator, to_find=signal, channel=channel)
                if use:
                    data_indicator = indicator_data(data)
                    message = _indicator_message_templater(data_indicator)
                    to_send.add_field(name=signal, value=message, inline=False)
            discord_messages.append((channel, to_send))
    # }

    # {
    # sending messages
    if len(discord_messages) > 0:
        logging.info('Sending discord messages')
        for message in discord_messages:
            channel = message[0]
            to_send = message[1]
            logging.info(f'message being prepared {channel}, {to_send}')
            # {
            # check for chart
            chart = None
            load_chart = False
            if discordbot['charts']:
                if channel.get('charts') is False:
                    load_chart = False
                else:
                    load_chart = True
            elif not discordbot['charts'] and channel.get('charts'):
                load_chart = True

            if load_chart:
                logging.info('Trying to load chart')
                try:
                    chart = discord.File(fp=f'{fh}.png')
                    logging.info('Chart found')
                except Exception as e:
                    logging.info(f'{e}: no charts recieved')
            else:
                logging.info('No chart setup')
            # }

            channel_id = bot.get_channel(channel.get('id'))
            await channel_id.send(embed=to_send, file=chart)
    else:
        logging.info('No messages found to send')
    # }

# {
# Docker setup -- DO NOT USE
# TODO fix and test
docker = aiodocker.Docker('http://192.168.65.0/28')
async def run_docker():
    #await create_image()
    if dockerimage['image']:
        logging.info('Running docker')
        container = await docker.containers.create_or_replace(
            config={'Cmd': ["/usr/local/bin/python", "app.py"], 'Image': dockerimage['image_name']},
            name='crypto-signal')
        logging.info(f'created and started container {container._id[:12]}')
        await container.start()
    else:
        logging.info('continuing without docker container creation')
# }

# {
# tornado setup
class MainHandler(tornado.web.RequestHandler):
    async def post(self):
        logging.info('Post Request')
        data = self.get_argument('data', 'No data recieved')
        self.write(data)
        msg = self.get_argument('messages', 'No data recieved')
        fname = None
        try:
            fileinfo = self.request.files['chart'][0]
            filename = fileinfo['filename']
            content_type = fileinfo['content_type']
            logging.info(f'filename is {filename}, content type: {content_type}')
            fname = fileinfo['filename']
            # extn = os.path.splitext(fname)[1]
            # cname = str(uuid.uuid4()) + extn
            fh = open(f'{fname}.png', 'wb')
            fh.write(fileinfo['body'])
        except KeyError as e:
            logging.info(f'{e}')
        await parse_message(json.loads(msg), fname)

    async def get(self):
        logging.info("Get Request")
        data = self.get_argument('data', 'No data recieved')
        self.write(data)
# }

if __name__ == '__main__':
    app = tornado.web.Application([(r"/", MainHandler)])
    port = 9999
    app.listen(port)
    logging.info(f'Listening on http://localhost:{port}')
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(bot.start(discordbot['token']), loop=loop)
    loop.run_forever()

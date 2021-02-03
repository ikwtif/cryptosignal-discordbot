
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



# # monkey patch du to 3.8 breaking change
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# bot setup
bot = commands.Bot(command_prefix="!")

def config():
    conf = Configuration()
    settings = conf.settings
    discordbot = conf.discordbot
    message_templater = conf.message
    dockerimage = conf.docker
    return settings, discordbot, message_templater, dockerimage


settings, discordbot, message_templater, dockerimage = config()

@bot.event
async def on_ready():
    print("the bot is ready")

@bot.command()
async def clear(ctx, amount=100):
    await ctx.channel.purge(limit=amount)

@bot.command()
async def test(ctx):
    await ctx.send("it works")


async def clear_messages(amount=100):
    chnls = list()
    for channel in discordbot['channels'].keys():
        if channel == 'channel_main':
            pass
        elif not (discordbot['channels'][channel]['id'] in chnls):
            chnls.append(discordbot['channels'][channel]['id'])
    for channel in chnls:
        channelid = bot.get_channel(int(channel))
        messages = await channelid.history().flatten()
        print(messages)
        print('deleting messages in channel: {}'.format(channel))
        await channelid.delete_messages(messages)


def _find_number(prices, text):
    f = re.search(text, prices)
    return f.group(1)


def _title_message_templater(messages):
    message_template = Template(message_templater['title_template'])
    new_title = str()
    base_currency, quote_currency, candle_period, market, date, exchange, prices, price_high, price_low, price_close = (str() for i in range(10))
    try:
        base_currency = messages[0]['base_currency']
        quote_currency = messages[0]['quote_currency']
        candle_period = messages[0]['analysis']['config']['candle_period']
        market = messages[0]['market']
        date = messages[0]['creation_date']
        exchange = messages[0]['exchange']
        if messages[0]['prices']:
            prices = messages[0]['prices']
            price_high = _find_number(prices, 'High: (\d+.)*\d+')
            price_low = _find_number(prices, 'Low: (\d+.)*\d+')
            price_close = _find_number(prices, 'Close: (\d+.)*\d+')

    except KeyError as error:
        print('title templater: the key {} does not exist'.format(error))

    new_title += message_template.render(base_currency=base_currency,
                                         quote_currency=quote_currency,
                                         candle_period=candle_period,
                                         market=market,
                                         date=date,
                                         exchange=exchange,
                                         prices=prices,
                                         price_high=price_high,
                                         price_low=price_low,
                                         price_close=price_close)
    return new_title


def save_content(messages):
    filename = messages[0]['analysis']['config']['candle_period']
    with open('{}.txt'.format(filename), 'wt') as out:
        pprint(messages, stream=out)
        print("printing message recieved and saved in {}.txt".format(filename))


def _indicator_message_templater(indicator):
    message_template = Template(message_templater['indicator_template'])
    new_message = str()
    status, last_status, values, candle_period, period_count = (str() for i in range(5))

    try:
        status = indicator.get('status', 'NA')
        last_status = indicator.get('last_status', 'NA')
        values = indicator['values']
        candle_period = str(indicator['analysis']['config'].get('candle_period', 'NA'))
        period_count = str(indicator['analysis']['config'].get('period_count', 'NA'))

    except KeyError as error:
        print('message templater: the key {} does not exist'.format(error))

    new_message += message_template.render(status=status,
                                           last_status=last_status,
                                           values=values,
                                           candle_period=candle_period,
                                           period_count=period_count)
    return new_message


async def parse_message(messages, fh):
    print(type(messages))
    print('mess', messages)
    save_content(messages)

    if discordbot['charts']:
        try:
            chart = discord.File(fp="{}.png".format(fh))
        except:
            print('no charts recieved')
    else:
        chart = None
    title = _title_message_templater(messages)
    to_send = discord.Embed(title=title,
                            type="rich")
    for indicator in messages:
        message = _indicator_message_templater(indicator)
        to_send.add_field(name=indicator['indicator'], value=message, inline=False)
    msg_candle_period = messages[0]['analysis']['config']['candle_period']
    msg_token = messages[0]['base_currency']
    channel = None
    channels_token = discordbot['channels_token']
    token_found = False
    for chan in channels_token.keys():
        if channels_token[chan].get('token') is None:
            pass
        else:
            if msg_token == str(channels_token[chan]['token']):
                channel = bot.get_channel(channels_token[chan]['id'])
                token_found = True
                break

    if not token_found:
        channels_candleperiod = discordbot['channels_candleperiod']
        for chnl in channels_candleperiod.keys():
            if channels_candleperiod[chnl].get('candle_period') is None:
                #do something? main channel if not defined?
                pass
            else:
                if msg_candle_period == str(channels_candleperiod[chnl]['candle_period']):
                    print('same')
                    channel = bot.get_channel(channels_candleperiod[chnl]['id'])
                    break
                elif msg_candle_period != str(channels_candleperiod[chnl]['candle_period']):
                    print('not same')

    if channel is None:
        channel = bot.get_channel(channels_candleperiod['channel_5']['id'])

    await channel.send(embed=to_send, file=(chart))


docker = aiodocker.Docker('http://192.168.65.0/28')


async def run_docker():
    #await create_image()
    if dockerimage['image']:
        print('running docker')

        container = await docker.containers.create_or_replace(
            config={'Cmd': ["/usr/local/bin/python", "app.py"], 'Image': dockerimage['image_name']},
            name='crypto-signal')
        print("created and started container {}".format(container._id[:12]))
        await container.start()
    else:
        print('continuing without docker container creation')


# tornado setup
class MainHandler(tornado.web.RequestHandler):
    async def post(self):
        print('post request')
        data = self.get_argument('data', 'No data recieved')
        self.write(data)
        msg = self.get_argument('messages', 'No data recieved')
        fname = None
        if discordbot['charts']:
            try:
                fileinfo = self.request.files['chart'][0]
                print('filename is {}, content type: {}'.format(fileinfo['filename'], fileinfo['content_type']))
                fname = fileinfo['filename']
                # extn = os.path.splitext(fname)[1]
                # cname = str(uuid.uuid4()) + extn
                fh = open("{}.png".format(fname), 'wb')
                fh.write(fileinfo['body'])
            except KeyError as e:
                print(e)
        print(msg)
        await parse_message(json.loads(msg), fname)

    async def get(self):
        print("Get Request")
        data = self.get_argument('data', 'No data recieved')
        self.write(data)


if __name__ == '__main__':
    app = tornado.web.Application([(r"/", MainHandler)])
    app.listen(9999)
    print("Listening on http://localhost:{}".format(9999))
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(bot.start(discordbot['token']), loop=loop)
    loop.run_forever()


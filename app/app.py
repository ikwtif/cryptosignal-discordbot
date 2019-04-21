import tornado.ioloop
import tornado.options
import tornado.web
import tornado.platform.asyncio
import json
import aiodocker
import asyncio
import re
from tornado.options import define, options
from jinja2 import Template
from pprint import pprint
from conf import Configuration
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='>')


def config():
    conf = Configuration()
    settings = conf.settings
    discordbot = conf.discordbot
    message_templater = conf.message
    return settings, discordbot, message_templater


settings, discordbot, message_templater = config()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)

    channel = bot.get_channel(discordbot['channel_id'])
    print('Using chanel ', str(channel))

    await channel.send('Hello hello!')


def _find_number(prices, text):
    f = re.search(text, prices  )
    return f.group(1)


def _title_message_templater(messages):

    message_template = Template(message_templater['title_template'])
    new_title = str()
    base_currency, quote_currency, market, date, exchange, prices, price_high, price_low, price_close = (str() for i in range(9))

    try:
        base_currency = messages[0]['base_currency']
        quote_currency = messages[0]['quote_currency']
        market = messages[0]['market']
        date = messages[0]['creation_date']
        exchange = messages[0]['exchange']
        prices = messages[0]['prices']
        price_high = _find_number(prices, 'High: (\d+.)*\d+')
        price_low = _find_number(prices, 'Low: (\d+.)*\d+')
        price_close = _find_number(prices, 'Close: (\d+.)*\d+')

    except:
        pass

    new_title += message_template.render(base_currency=base_currency,
                                         quote_currency=quote_currency,
                                         market=market,
                                         date=date,
                                         exchange=exchange,
                                         prices=prices,
                                         price_high=price_high,
                                         price_low=price_low,
                                         price_close=price_close)
    return new_title


def _indicator_message_templater(indicator):
    message_template = Template(message_templater['indicator_template'])
    new_message = str()
    status, last_status, values, candle_period, period_count = (str() for i in range(5))

    try:
        status = indicator['status']
        last_status = indicator['last_status']
        if len(indicator['values'].keys()) > 1:
            values = indicator['values']
        else:
            values = indicator['values'][indicator['indicator']]
        candle_period = str(indicator['analysis']['config']['candle_period'])
        period_count = str(indicator['analysis']['config']['period_count'])
    except:
        pass

    new_message += message_template.render(status=status,
                                           last_status=last_status,
                                           values=values,
                                           candle_period=candle_period,
                                           period_count=period_count)
    return new_message


async def parse_message(messages, fh):
    await save_content(messages)
    channel = bot.get_channel(discordbot['channel_id'])
    chart = discord.File(fp="{}.png".format(fh))
    title = _title_message_templater(messages)
    to_send = discord.Embed(title=title,
                            type="rich")
    for indicator in messages:
        message = _indicator_message_templater(indicator)
        to_send.add_field(name=indicator['indicator'], value=message, inline=False)

    await channel.send(embed=to_send, file=chart)


async def save_content(messages):
    with open('messages.txt', 'wt') as out:
        pprint(messages, stream=out)
        print("printing message recieved and saved in messages.txt")


class MainHandler(tornado.web.RequestHandler):

    async def post(self):
        print('post request')
        data = self.get_argument('data', 'No data recieved')
        self.write(data)
        msg = self.get_argument('messages', 'No data recieved')

        fileinfo = self.request.files['chart'][0]
        print('filename is {}, content type: {}'.format(fileinfo['filename'], fileinfo['content_type']))
        fname = fileinfo['filename']
        # extn = os.path.splitext(fname)[1]
        # cname = str(uuid.uuid4()) + extn
        fh = open("{}.png".format(fname), 'wb')
        fh.write(fileinfo['body'])

        await parse_message(json.loads(msg), fname)


    def get(self):
        print("Get Request")
        data = self.get_argument('data', 'No data recieved')
        self.write(data)


async def run_docker():
    print('running docker')
    docker = aiodocker.Docker()
    img = 'dev/cryptosignals:latest'
    container = await docker.containers.create_or_replace(
        config={'Cmd': ["/usr/local/bin/python", "app.py"], 'Image': img},
        name='crypto-signal')
    print("created and started container {}".format(container._id[:12]))
    await container.start()


def run_tornado():
    print("running tornado")
    define("port", default=9999, help="run ont he given port", type=int)
    tornado.options.parse_command_line()
    application = tornado.web.Application([(r"/", MainHandler)])
    application.listen(options.port)
    print("Listening on http://localhost:{}".format(options.port))


async def run_discordbot():
    print('bot running')
    await bot.run(discordbot['token'])


if __name__ == "__main__":
    run_tornado()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(run_discordbot())
    asyncio.ensure_future(run_docker())
    loop.run_forever()
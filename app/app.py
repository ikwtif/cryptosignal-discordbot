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
from io import BytesIO
from aiodocker import utils
import discord
from discord.ext import commands
from datetime import datetime, timedelta

bot = commands.Bot(command_prefix='>')


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
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)

    channel = bot.get_channel(discordbot['channels']['channel_main']['id'])
    print('Using chanel ', str(channel))

    await channel.send('Hello hello!')

@bot.command()
async def clear(ctx, amount=100):
    await ctx.channel.purge(limit=amount)


post_time = datetime.utcnow()
print(post_time)
#trigger = 0

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


def _indicator_message_templater(indicator):
    message_template = Template(message_templater['indicator_template'])
    new_message = str()
    status, last_status, values, candle_period, period_count = (str() for i in range(5))

    try:
        status = indicator.get('status', 'NA')
        last_status = indicator.get('last_status', 'NA')
        values = indicator['values']
        '''
        if len(indicator['values'].keys()) > 1:
            values = indicator['values']
        else:
            values = indicator['values'][indicator['indicator']]
        '''
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
    await save_content(messages)
    """
    global trigger
    global post_time

    time = messages[0]['creation_date']
    posted_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    diff = posted_time - post_time
    difference = diff.total_seconds()
    print('diff', difference)
    #timedelta(seconds=110)
    if diff.total_seconds() > 20:
        await clear_messages()
        await asyncio.sleep(5)
        print('sleeping?')
    post_time = datetime.utcnow()
    """

    '''FIGURE OUT HOW TO AUTOMATICALLY REMOVE MESSAGES IN CHANNEL WHEN GETTING MULTIPLE POSTS PER NOTIFICATION RUN
    VERIFY AGAINST CREATION DATE????
    
    global trigger
    global post_time
    trigger = trigger + 1    
    if post_time > datetime.now() - timedelta(seconds=-60) and trigger > 1:
        print('~'*20)
        print(post_time)
        print(trigger)
        print('clearing messages')
        post_time = datetime.now()
        await clear_messages()
    #await clear_messages()
    '''
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

    channels = discordbot['channels']
    for chnl in channels.keys():
        if channels[chnl].get('candle_period') is None:
            #do something? main channel if not defined?
            pass
        else:
            if msg_candle_period == str(channels[chnl]['candle_period']):
                channel = bot.get_channel(channels[chnl]['id'])

    await channel.send(embed=to_send, file=(chart))


async def save_content(messages):
    filename = messages[0]['analysis']['config']['candle_period']
    with open('{}.txt'.format(filename), 'wt') as out:
        pprint(messages, stream=out)
        print("printing message recieved and saved in {}.txt".format(filename))


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

docker = aiodocker.Docker()

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
'''
async def create_image():
    name = "{}:latest".format(dockerimage['image_name'])
    dockerfile= """
    FROM python:3.6-jessie
    
    # TA-lib is required by the python TA-lib wrapper. This provides analysis.
    COPY lib/ta-lib-0.4.0-src.tar.gz /tmp/ta-lib-0.4.0-src.tar.gz
    
    RUN cd /tmp && \
      tar -xvzf ta-lib-0.4.0-src.tar.gz && \
      cd ta-lib/ && \
      ./configure --prefix=/usr && \
      make && \
      make install
    
    ADD /home/ikwtif/PycharmProjects/crypto-signal/app/requirements-step-1.txt /app/requirements-step-1.txt
    ADD /home/ikwtif/PycharmProjects/crypto-signal/app/requirements-step-2.txt /app/requirements-step-2.txt
    WORKDIR /home/ikwtif/PycharmProjects/crypto-signal/app
    
    # Pip doesn't install requirements sequentially.
    # To ensure pre-reqs are installed in the correct
    # order they have been split into two files
    RUN pip install -r requirements-step-1.txt
    RUN pip install -r requirements-step-2.txt
    
    CMD ["/usr/local/bin/python","app.py"]
    """

    f = BytesIO(dockerfile.encode("utf-8"))
    tar_obj = utils.mktar_from_dockerfile(f)
    await docker.images.build(fileobj=tar_obj, encoding="gzip", tag=name)
    tar_obj.close()
    image = await docker.images.inspect(name=name)
    assert image
'''

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
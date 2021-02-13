# Cryptosignal-discordbot

Discordbot for use with CryptoSignal Development branch (https://github.com/CryptoSignal/crypto-signal/tree/develop)

## Getting Started
See Docker or Docker-compose section for starting the app. Docker-compose let's you test out the app/configurations 
without having to rebuild the docker image every time. 
See Crytpo-Signal section for setting up a Crypto-Signal webhook to send data to the bot.
See Config File for the options, make your own config file and name it configBot.yml and put it in the app folder. 

## Docker 

In the terminal screen go to the main folder, then excecute the following commands (image_name can be any name you want)
  1. Builds a docker image 
  2. Starts a docker container
```
docker build -t image_name .
docker run -d --rm -p 9999:9999 image_name
```
For Crypto-Signal
  1. Builds a docker image
  2. Starts a docker container. 
  
Change PATH_TO_APP_FOLDER to your path of the app folder inside crypto-signal

```
docker build -t signal .
docker run -it --rm --net="host" -v PATH_TO_APP_FOLDER:/app signal
```

## Docker-compose
1. Build a docker image
2. Run/Restart the container with the following command 
```
docker build -t bot .
docker-compose -f docker-compose.dev.yml up
```
The image name and port number (default: 9999:9999) are defined in the docker-compose.dev.yml file. 
You can change those there if you want.


## Crypto-Signal

To create a connection you should set up a webhook notifier inside the config.yml file for crypto-signal.
You can use the url from the example if both are running on the same machine and if you run the crytpo-signal docker 
container with the `--net="host"` flag. If there are issues you can check the route Gateway for the Discordbot 
Docker container and use that. Or run both without Docker.

Example:
```
notifiers:
  webhook:
    required:
      url: http://127.0.0.1:9999
    optional:
      username: null
      password: null
```

## Configuration File 

Create your own configuration file called `configBot.yml` for use with the app.
See the `configBotDefault.yml` file for a full example configuration file. 

##### Setup Discordbot

- charts: define whether or not you want to post charts with the messages (make sure crypto-signal has charts on as well). 
You can individually toggle these in the channels as well.
- token: requires your discord bot token
- channels: here you define the channels from the discord server you want to send the messages to 

```
# setup for discordbot
discordbot:
  charts:
  token: 
  channels:
```

##### Channels
The app allows you to set up different discord channels. 
You can define multiple combinations of base currency / quote currency / indicators / candle_periods for one channel,
if you use `all`, that means every indicator crypto-signal sends gets used. Use the naming scheme as defined by crypto-signal, they should match. 
For candle periods, If you want to use weeks and months, see this PR for crypto-signal:https://github.com/CryptoSignal/Crypto-Signal/pull/393 

Every name for a channel, except channel_notfound (ex. `channel_1`) should be unique but can be custom.
You can leave out channel_notfound if you do not want this functionality, this is used for posting a message to discord if a channel is not found and can be used for testing.

The configuration "title_indicator:true" is when you want to use indicator data inside the title of a discord message, 
this is only available when you set up only 1 indicator for the channel. You can still use the other parts of a 
discord message.

- id: your channel id from discord
- base_currency: the base currency you want (can be one, multiple, or all)
- quote_currency: the quote currency you want (can be one, multiple, or all)
- candle-period: the candle period you want 
- indicator: the indicators you want
- message: the template you want to use (uses `default` if it's not defined)

See quote_currency for how to properly define multiples, anything with multiples defined needs to follow that formatting

**optional** 
- charts: toggle charts for specific channel
- title_indicator: for when you want indicator data used in the title of a discord message, only use this when you set up 1 indicator for the channel
```
channel_1:
  id: channel_id
  base_currency: ETH
  quote_currency:
    - USDT
    - BTC
  candle_period: all
  indicator: all
  charts: false
  title_indicator: false
  message: default
```

##### Messages

Under the message section you can define templates you want to use for the discord messages. 

The structure for a discord message:
 1. title
 2. 1 or more fields consisting of name and value 
 (can be used for different indicators, unless you want indicator data in the title, which will only create 1 field)
 
You can set the template for all these, they can't be empty so use a character if you don't want data in a part.
Use these names to define the templates in the config.

```
{message title}
[title]
---------------
{message}
[name]
[value]
```
a template setup should look like this, with default being the name of the template, which you can define in a channel
Messages use Jinja2 templating.
``` 
messages:
  default:
    title: "{{base_currency}}, {{quote_currency}}, {{market}}, {{exchange}} {{candle_period}}
            {{ '\n' -}} High: {{price_high}}, Low: {{price_low}}, Close: {{price_close}}
            {{ '\n' -}} {{date}}
            {{ '\n' -}} https://tradingview.com/symbols/{{base_currency}}{{quote_currency}}"
    name: "{{indicator}}"
    value: "value: {{values}}
            {{ '\n' -}} status: {{status}}
            {%- if status == 'hot' %} :rocket: {%- else %} :cry: {%- endif -%}
            {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}"
```

##### Current Options for Jinja2 template
```
title:
base_currency | quote_currency | candle_period | market | date | exchange | prices| price_high | 
price_low | price_close | candle_period | period_count

value: (+ what's in title)
values | candle_period | period_count| status | last_status | hot_label | cold_label | indicator_label | hot_cold_label

name: (+ what's in title)
values | candle_period | period_count| status | last_status | hot_label | cold_label | indicator_label | hot_cold_label
```

if you set up `title_indicator:true` in a channel you can use everything in the title setup as well.

### Prerequisites

see requirements.txt

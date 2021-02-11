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

The app allows you to set up different discord channels. 
You can define multiple combinations of base currency/quote currency/indicators/candle_periods for one channel,
`all` means any go. Use the naming scheme as defined by crypto-signal, they should match. 
For candle periods, If you want to use weeks and months, see this PR for crypto-signal:https://github.com/CryptoSignal/Crypto-Signal/pull/393 

Every name for a channel, except channel_notfound (ex. `channel_1`) should be unique but can be custom.
You can leave out channel_notfound if you do not want this functionality. 

Only use the "title:true" option with a setup for 1 indicator. This will put everything in the title section of a 
discord message and will use title_indicator_template for creating the message. 
You can use name_message to have data in the name field of the discord message, this defaults to the indicator name. 

```
# setup for discordbot
discordbot:
  charts: false
  # true -> posts charts in all channels or define "charts:false" in the channel where you do not want charts to be posted
  # false -> you can still define "charts:true" per channel
  token: discordbot_token
  channels:
    channel_1:
      id: channel_id
      base_currency: ETH
      quote_currency:
        - USDT
        - BTC
      candle_period: all
      indicator: all
    channel_2:
      id: channel_id
      base_currency: all
      quote_currency: all
      candle_period: all
      indicator:
        - momentum
        - bollinger
        - macd
        - ichimoku
      charts: true
    channel_3:
      id: channel_id
      base_currency: all
      quote_currency: all
      candle_period: all
      indicator:
        - momentum
      charts: false
      title: true
  channel_notfound:
    # used when a channel is not found for a token/indicator
    id: channel_id
    base_currency: all
    quote_currency: all
    candle_period: all
    indicator: all
```

Messages use Jinja2 templating, see the example.

```
message:
  title_template: "{{base_currency}}, {{quote_currency}}, {{market}}, {{exchange}} {{candle_period}}
                  {{ '\n' -}} High: {{price_high}}, Low: {{price_low}}, Close: {{price_close}}
                  {{ '\n' -}} {{date}}
                  {{ '\n' -}} https://tradingview.com/symbols/{{base_currency}}{{quote_currency}}"
  indicator_template: "value: {{values}}
                      {{ '\n' -}} status: {{status}}
                      {%- if status == 'hot' %} :rocket: {%- else %} :cry: {%- endif -%}
                      {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}"
  title_indicator_template: "{{base_currency}}, {{quote_currency}}, {{market}}, {{exchange}} {{candle_period}}
                             {{ '\n' -}} High: {{price_high}}, Low: {{price_low}}, Close: {{price_close}}
                             {{ '\n' -}} {{date}}
                             {{ '\n' -}} https://tradingview.com/symbols/{{base_currency}}{{quote_currency}}
                             {{ '\n' -}} value: {{values}}
                             {{ '\n' -}} status: {{status}}
                             {%- if status == 'hot' %} :rocket: {%- else %} :cry: {%- endif -%}
                             {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}"
  name_message_template: "{{indicator}}"

```
##### Current Options
```
title template:
base_currency | quote_currency | candle_period | market | date | exchange | prices| price_high | 
price_low | price_close | candle_period | period_count

indicator template:
values | candle_period | period_count| status | last_status | hot_label | cold_label | indicator_label | hot_cold_label

title_indicator_template: 
everything mentioned

name_template:
everything mentioned

```

### Prerequisites

see requirements.txt

# Cryptosignal-discordbot

Discordbot for use with CryptoSignal Development branch (https://github.com/CryptoSignal/crypto-signal/tree/develop)

## Getting Started
####DOES CURRENTLY NOT WORK. 
####See Docker and Docker-compose section for how to run with Docker

If you want to use the Discordbot with a docker image for crypto-signal.

Set up a docker image from CryptoSignal development branch.
Building the docker image (config file used should be inside app folder when building image):

  In the dockerfile add the following line
  
    `ADD app/ /app`
    
  Then build image with:
  
    `docker build . -t [your image name]`


Create Config file for discordbot as `configBot.yml` and add the following
```
docker:
  image: true
  image_name: [your image name]
```

## Config File

The following allows you to setup channels with seperated candle_periods. 
Create channels for every candle_period you are sending to the bot. 
The main channel is just used to post a `hello!` message when the bot starts. 
You can define multiple combinations of tokens/indicators for one channel,`all` means any go.

Use tokens/indicators names as defined by crypto-signal, they should match. 
Use candle_periods as defined by crypto-signal, they should match. If you want to use weeks and months, see this PR for crypto-signal:https://github.com/CryptoSignal/Crypto-Signal/pull/393 

Every name for a channel, except channel_notfound (ex. `channel_1`) should be unique inside their main channel 
(`channels_token`, `channels_candleperiod`) but can be anything.

```
discordbot:
  charts: false
  token: your_discordbot_token
  channels_token:
    # channels based on the token you want to send to the channel
    channel_1:
      token: BTC
      id: your_discord_channel_id
      indicator: 
        - momentum
        - iiv
  channels_candleperiod:
    # channels based on the candle period you want to send to the channel
    channel_1:
      token: all
      candle_period: 5m
      id: your_discord_channel_id
      indicator: all
    channel_2:
      token: ETH
      candle_period: 1d
      id: your_discord_channel_id
      indicator: all
  channel_notfound:
    # used when a channel is not found for a token/indicator
    token: all
    id: your_discord_channel_id
    indicator: all
```

#### One Indicator setup
```
message:
  # only set indicator to false if you are sending one indicator
  # and you want to use the indicator data in the title_template
  title: true
  indicator: true
```

Messages use Jinja2 templating, see the example for most options.

```
message:
  title_template: "{{base_currency}}, {{quote_currency}}, {{market}}, {{exchange}} {{candle_period}}
                  {{ '\n' -}} High: {{price_high}}, Low: {{price_low}}, Close: {{price_close}}
                  {{ '\n' -}} {{date}}
                  {{ '\n' -}} https://tradingview.com/symbols/{{base_currency}}{{quote_currency}}"
  indicator_template: "value: {{values}}
                      {{ '\n' -}} status: {{status}}
                      {%- if status == 'hot' %} :rocket: {%- else %} :cry: {%- endif -%}
                      {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}
                      {{ '\n' -}} candles: {{candle_period}}"
```
##### Current Options
```
title template:
base_currency | quote_currency | candle_period | market | date | exchange | prices| price_high | 
price_low | price_close | candle_period | period_count

indicator template (can be used with title template for a 1 indicator setup):
values | candle_period | period_count| status | last_status | hot_label | cold_label | indicator_label 
```

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

## Docker 

In the terminal screen go to the main folder, then excecute the following commands (image_name can be any name you want)
  1. Builds a docker image 
  2. Starts a docker container
```
docker build -t image_name .
docker run -d -p 9999:9999 image_name
```
For Crypto-Signal
  1. Builds a docker image
  2. Starts a docker container. 
  
Change PATH_TO_APP_FOLDER to your the path of the app folder inside crypto-signal

```
docker build -t signal .
docker run -it --net="host" -v PATH_TO_APP_FOLDER:/app signal
```

## Docker-compose
1. Build a docker image
2. Run/Restart the container with the following command 
```
docker build -t image_name .
docker-compose -f docker-compose.dev.yml up
```

### Prerequisites

see requirements.txt

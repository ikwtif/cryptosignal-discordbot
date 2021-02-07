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

The following allows you to setup channels. 
You can define multiple combinations of base currency/quote currency/indicators/candle_periods for one channel,
`all` means any go. Use the naming scheme as defined by crypto-signal, they should match. 
For candle periods, If you want to use weeks and months, see this PR for crypto-signal:https://github.com/CryptoSignal/Crypto-Signal/pull/393 

Every name for a channel, except channel_notfound (ex. `channel_1`) should be unique but can be custom.
You can leave out channel_notfound if you do not want this functionality. 

Only use the "title:true" option with a setup for 1 indicator. This will put everything in the title section of a 
discord message and will use title_indicator_template. 

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
                      {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}"
  title_indicator_template: "{{base_currency}}, {{quote_currency}}, {{market}}, {{exchange}} {{candle_period}}
                             {{ '\n' -}} High: {{price_high}}, Low: {{price_low}}, Close: {{price_close}}
                             {{ '\n' -}} {{date}}
                             {{ '\n' -}} https://tradingview.com/symbols/{{base_currency}}{{quote_currency}}
                             {{ '\n' -}} value: {{values}}
                             {{ '\n' -}} status: {{status}}
                             {%- if status == 'hot' %} :rocket: {%- else %} :cry: {%- endif -%}
                             {%- if period_count -%} {{ '\n' -}} period: {{period_count}} {%- endif -%}"
```
##### Current Options
```
title template:
base_currency | quote_currency | candle_period | market | date | exchange | prices| price_high | 
price_low | price_close | candle_period | period_count

indicator template (can be used with title template for a 1 indicator setup):
values | candle_period | period_count| status | last_status | hot_label | cold_label | indicator_label | hot_cold_label
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
docker run -it --rm --net="host" -v PATH_TO_APP_FOLDER:/app signal
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

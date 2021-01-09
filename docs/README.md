# Cryptosignal-discordbot

Discordbot setup for use with CryptoSignal Development branch (https://github.com/CryptoSignal/crypto-signal/tree/develop)

## Getting Started

If you want to use it with a docker image 
(This also builds with the config file so only use it if you know you won't change the config or you will have to rebuild the Image each time you want to make changes).

Set up a docker image from CryptoSignal development branch (https://github.com/CryptoSignal/crypto-signal)
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

The following allows you to setup channels with seperated candle_periods. Create channels for every candle_period you are sending to the bot. The main channel is just used to post a `hello!` message when the bot starts. Ofcourse, you can just add one channel id to all of them if you want to post everything in one channel. 

```
discordbot:
  charts: false
  token:
  channels:
    channel_main:
      id:
    channel_1:
      candle_period: 1h
      id:
    channel_2:
      candle_period: 4h
      id:
    channel_3:
      candle_period: 1d
      id:
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

## Crypto-Signal

To create a connection you should set up a webhook notifier inside the config.yml file.

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

### Prerequisites

see requirements.txt

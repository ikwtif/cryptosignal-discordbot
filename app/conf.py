"""Load configuration from environment
"""

import os
import yaml
import logging
import glob

class Configuration:
    """Parses the environment configuration to create the config objects.
    """

    def __init__(self, logging):
        """Initializes the Configuration class
        """
        logging.info('loading configuration file')
        for name in glob.glob('*.yml'):
            if name.lower() == 'configbot.yml':
                with open(name, 'r') as config_file:
                    user_config = yaml.load(config_file, Loader=yaml.FullLoader)
                    break
        if not user_config:
            raise Exception('No configuration file exists')

        self.settings = user_config.get('settings')
        self.discordbot = user_config.get('discordbot')
        self.docker = user_config.get('docker')
        self.messages = user_config.get('messages')
        if not self.settings:
            logging.info('Missing settings, using defaults')
        if not self.discordbot:
            raise Exception('Missing discordbot setup')
        if not self.docker:
            logging.info('Missing settings for docker, no problem, is not used')
        if not self.messages:
            raise Exception('Missing settings for message template')

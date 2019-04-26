"""Load configuration from environment
"""

import os
import yaml

class Configuration():
    """Parses the environment configuration to create the config objects.
    """

    def __init__(self):
        """Initializes the Configuration class
        """

        if os.path.isfile('configBot.yml'):
            with open('configBot.yml', 'r') as config_file:
                user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        else:
            user_config = dict()

        if 'settings' in user_config:
            self.settings = user_config['settings']
        else:
            raise Exception("no settings")

        if 'discordbot' in user_config:
            self.discordbot = user_config['discordbot']

        if 'docker' in user_config:
            self.docker = user_config['docker']

        else:
            raise Exception("no bot configured")

        if 'message' in user_config:
            self.message = user_config['message']
        else:
            raise Exception("no message configured")
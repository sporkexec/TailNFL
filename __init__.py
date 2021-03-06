###
# Copyright (c) 2013, Jacob Courtneay
# All rights reserved.
#
#
###

"""
Provides live play-by-play announcements for NFL games.
"""

import supybot
import supybot.world as world

# Use this for the version of this plugin.  You may wish to put a CVS keyword
# in here if you're keeping the plugin in CVS or some similar system.
__version__ = "0.0"

# Replace this with an appropriate author or supybot.Author instance.
__author__ = supybot.Author('Jacob Courtneay', 'sporkexec',
                            'jacob@sporkexec.com')

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = {}

# This is a url where the most recent plugin package can be downloaded.
__url__ = 'https://github.com/sporkexec/TailNFL'

from . import config
from . import plugin
from imp import reload
# In case we're being reloaded.
reload(config)
reload(plugin)
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!
import nflgame
import nflgame.live
reload(nflgame)
reload(nflgame.live)

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

###
# Copyright (c) 2013, Jacob Courtneay
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import nflgame
import nflgame.live
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('TailNFL')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

team_names = {t[0]: t[1]+' '+t[2] for t in nflgame.teams}

def actually_threaded(f):
    """Makes sure a command spawns a NEW thread when called.
    supybot.commands.thread() seems to just ensure that the module is running
    in a separate thread, but sometimes we need individual functions
    threaded. (Say, the main loop which does sleep() waits.) This is probably
    the wrong way to do this; improvements are welcome."""
    def newf(self, irc, msg, args, *L, **kwargs):
        realargs = (self, irc, msg, args) + tuple(L)
        t = world.SupyThread(target=f, args=realargs, kwargs=kwargs)
        t.setDaemon(True)
        t.start()
    return utils.python.changeFunctionName(newf, f.func_name, f.__doc__)

class TailGame:
    def __init__(self, game, irc, chan, chan_index, module):
        self.game = game
        self.irc = irc
        self.chan = chan
        self.chan_index = chan_index
        self.module = module
        self.home = self.game.home
        self.away = self.game.away
        self.home_long = team_names[self.home]
        self.away_long = team_names[self.away]
        self.topic = ''
        self.topic_update()
        self.module.privmsg("Now playing in %s, %s at %s" % (self.chan, self.away_long, self.home_long))
        self.privmsg("Now playing: %s at %s" % (self.away_long, self.home_long))

    def privmsg(self, msg):
        self.irc.sendMsg(ircmsgs.privmsg(self.chan, msg))

    def diff_handle(self, gamediff):
        self.game = gamediff.after
        for play in gamediff.plays:
            self.play_handle(play, (play is gamediff.plays[-1]))
        self.topic_update()

    def play_handle(self, play, is_last):
        team = ''
        down = ''
        nowdown = ''
        if play.team:
            team = play.team + ": "
        if play.down and play.yards_togo:
            down = play.down
            down = str(down) + ('0PS!', 'st', 'nd', 'rd', 'th')[down] + " & " + str(play.yards_togo)
            down = "[%s] " % down
        if is_last and self.game.down:
            nowdown = ' Now %s.' % self.get_down()
        self.privmsg(team + down + play.desc + nowdown)

    def get_down(self):
        down = self.game.down
        down = str(down) + ('0PS!', 'st', 'nd', 'rd', 'th')[down]
        yards = str(self.game.togo)
        return down+" & "+yards

    def get_quarter(self):
        if self.game.time.is_pregame():
            q = 'Pregame'
        elif self.game.time.is_halftime():
            q = 'Halftime'
        elif self.game.time.is_final():
            q = 'Final'
        else:
            q = self.game.time.quarter
            if q > 3: q -= 1 # Halftime is the 3rd quarter for some reason =\
            q = str(q) + ('0PS!', 'st', 'nd', 'rd', 'th')[q] + ' quarter'
        return q

    def topic_update(self):
        score = self.game.nice_score()
        quarter = self.get_quarter()
        topic = "%s - %s" % (score, quarter)
        if topic != self.topic:
            self.topic = topic
            self.irc.sendMsg(ircmsgs.topic(self.chan, self.topic))

class TailNFL(callbacks.Plugin):
    """Provides live play-by-play announcements for NFL games.
    Use "tailnflinit" to begin the main loop and start announcing events.
    Use "listgames" to get a list of ongoing games and their channels."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TailNFL, self)
        self.__parent.__init__(irc)

        self._chan_lobby = '##tailnfl'
        self._chan_format = '##tailnfl-game%s' # chan = format % index
        self._chans_used = [] # int list of occupied chans
        self._games = {}
        self._irc = irc

        self._irc.sendMsg(ircmsgs.join(self._chan_lobby))
        self._irc.sendMsg(ircmsgs.joins([self._chan_format%str(i) for i in range(1, 10)]))

    @actually_threaded
    def tailnflinit(self, irc, msg, args):
        """takes no arguments

        Starts the main loop to poll and announce events."""
        self.privmsg('TailNFL is online.')
        nflgame.live.run(self._main_cb)
    tailnflinit = wrap(tailnflinit, ['owner'])

    def listgames(self, irc, msg, args):
        """takes no arguments

        Displays active games and which channel they are in."""
        if len(self._games):
            for tailgame in self._games.values():
                irc.reply("%s at %s in %s" % (tailgame.away_long, tailgame.home_long, tailgame.chan))
        else:
            irc.reply("No active games.") #TODO: Find next game in schedule.
    listgames = wrap(listgames)

    def privmsg(self, msg):
        self._irc.sendMsg(ircmsgs.privmsg(self._chan_lobby, msg))

    def _main_cb(self, active_games, finished_games, gamediffs):
        for game in active_games:
            if game.gamekey not in self._games:
                self._add_game(game)
        for diff in gamediffs:
            self._games[diff.before.gamekey].diff_handle(diff)
        for game in finished_games:
            if game.gamekey in self._games:
                self._del_game(game)
            else:
                self.privmsg('%s - Final (Untracked game)' % game.nice_score())

    def _add_game(self, game):
        # Find first open chan slot
        chan_index = 1
        chan_list = sorted(self._chans_used)
        while chan_index in chan_list:
            chan_index += 1
        # Take chan
        self._chans_used.append(chan_index)
        chan = self._chan_format % chan_index
        self._irc.sendMsg(ircmsgs.join(chan))
        # Initialize game
        self._games[game.gamekey] = TailGame(game, self._irc, chan, chan_index, self)

    def _del_game(self, game):
        tailgame = self._games[game.gamekey]
        self.privmsg('%s - Final (%s now open)' % (game.nice_score(), tailgame.chan))
        self._chans_used.remove(tailgame.chan_index)
        del self._games[game.gamekey]

Class = TailNFL
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

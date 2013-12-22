TailNFL is a Limnoria/Supybot plugin for providing live play-by-play data for
NFL games. Announcements in a lobby channel are made whenever games begin or
end, directing users to game-specific channels. Each game channel provides
overall game stats in the topic while displaying a summary of each play in
realtime.

### Dependencies ###

TailNFL depends on the [nflgame module](https://github.com/BurntSushi/nflgame).

TailNFL runs on Python 2.7 only.


### Etymology ###

TailNFL borrows its name from the [unix `tail` command](http://en.wikipedia.org/wiki/Tail_(Unix\)):
>tail has a special command line option -f (follow) that allows a file to be monitored. Instead of just displaying the last few lines and exiting, tail displays the lines and then monitors the file. As new lines are added to the file by another process, tail updates the display. This is particularly useful for monitoring log files.

Similarly, TailNFL displays ongoing updates about game activity.

# DiscordGamesInCommon
Ever haning out with your friends in discord trying to pick a game for you and your friends to play together only to suggest games one or multiple people don't own? Well no more, with the Games In Common Discord bot you can quickly and easily find out what Steam games you all have in common and even have it pick one for you to play, except Age 2 of course.
The bot is written in Python 3 and using a Postgres database Docker image.

## Usage
To use the bot you simply need to direct message the bot either your Steam profile URL or your Steam64 ID and you are ready to go once you have added the bot to your server.
For the bot to be able to see what games you own, you will need your Steam profile to be public.

## Commands
!games
- Lists the games that all players in the player's channel have in common.

!spinthewheel
- Picks a random game from all the games that all the players in the player's current have in common except for Age 2.

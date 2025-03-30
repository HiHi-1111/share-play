# Shareplay

This is a project that allows people to play Roblox on other people's computers remotely. This game was made as a detour while attempting to build an effective Roblox bot.

## Motivating Problem

### A general-purpose Roblox bot.

A general-purpose Roblox bot is as follows:

1. Can be used to mimick ANY player action on Roblox

    Although it is fairly easy to make a Bot that does a simple click sequence on repeat, making a bot that executes more advanced mouse or keyboard actions is difficult.

2. Successfully bypasses Roblox's anti-bot features

    Roblox's anti-bot features make it nearly impossible to make bots that play even fairly simple games.

3. Can be adapted to play ANY Roblox game


## What Shareplay Does

Shareplay's goal is to make it easier to build a Roblox bot by first replacing a player by a remote player. If player actions can be implemented remotely, then replacing the remote player with a bot can be used to bypass Roblox's anti-bot feature that guards against local bots.


## Drawbacks

### Security

The host gives away access to their mouse input to the remote player. This is a terrible feature in terms of security. A malicious remote player can use this to access the host's computer and cause havoc.

### Rough Mouse Movements

The pointer moves in jumps as opposed to a smooth motion that follows the remote player exactly.

### Unmatching screen ratios

Even though, the mouse motion from the remote player is adjusted to size, it is not necessarily adjusted to the screen ratio of the host.

### Inflexible settings

There needs to be an option to relative mouse movements between remote player and host.

## Future Work

1. Adjusting the pointer motion to deal with the not-so-great aspects mentioned eariler.
2. Improve the user friendliness. Make the steps self-explanatory. 
3. Make it easier to set up in the first place. 
4. Make an executable. 
5. Restrict keyboard/mouse access to be only for Roblox. 

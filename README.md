# Group Editor Bot

Small bot that manages editors for a group,
and resends it when new people join.

The flagship instance is: <groupedit@nine.testrun.org>

It can also generate invitation QRs for your private Delta Chat groups. The bot is always online
and can add people to groups in "real time" while if you use your own invitation QRs, others will not be able
to join until you are online.

## Install

Binary releases can be found at: https://github.com/deltachat-bot/group-editor-bot/releases

To install from source:

```sh
go install github.com/deltachat-bot/group-editor-bot@latest
```

### Installing deltachat-rpc-server

This program depends on a standalone Delta Chat RPC server `deltachat-rpc-server` program that must be
available in your `PATH`. For installation instructions check:
https://github.com/deltachat/deltachat-core-rust/tree/master/deltachat-rpc-server

## Running the bot

Configure the bot:

```sh
group-editor-bot init bot@example.com PASSWORD
```

Start the bot:

```sh
group-editor-bot serve
```

Run `group-editor-bot --help` to see all available options.


## Usage in Delta Chat

Once the bot is running:

1. Add the bot address to some group in Delta Chat.
2. Send `/editor` to the group.
3. The bot will post an editor to the group
4. When new people are added to the group,
   they will already see the editor.


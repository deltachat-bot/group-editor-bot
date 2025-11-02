# Group Editor Bot

Small bot that manages editors for a group,
and resends it when new people join.

The flagship instance is: [groupedit@nine.testrun.org](https://i.delta.chat/#AB68F428FCEF88D32B46189314FDBB18B2789654&a=groupedit%40nine.testrun.org&n=Group%20Editor%20Bot&i=Ggt6rA8fZ89DCKXU2eOBXAOy&s=wdoG_ZGB15llV69gLG_sFCZw)

It can also generate invitation QRs for your private Delta Chat groups. The bot is always online
and can add people to groups in "real time" while if you use your own invitation QRs, others will not be able
to join until you are online.

## Install

To install from source:

```sh
git clone https://github.com/deltachat-bot/group-editor-bot
cd group-editor-bot
python3 -m venv venv
. venv/bin/activate
pip install .
```

## Running the bot

Configure & start the bot:

```sh
group-editor-bot --email groupedit@example.org --password s3cr3t
```

Run `group-editor-bot --help` to see all available options.

## Usage in Delta Chat

Once the bot is running:

1. Add the bot address to some group in Delta Chat.
2. Send `/editor` to the group.
3. The bot will post an editor to the group
4. When new people are added to the group,
   they will already see the editor.

## Development

PRs welcome :)

You can run lint and tests to ensure code quality and functionality:

```
pip install -e .[dev]
CHATMAIL_DOMAIN=nine.testrun.org tox
```


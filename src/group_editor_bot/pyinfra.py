import importlib.resources
from io import StringIO

from pyinfra.operations import files, git, server, systemd


def deploy_group_editor_bot(
    unix_user: str, bot_email: str, bot_passwd: str, dbdir: str = None
):
    """Deploy Group Editor Bot to a UNIX user, with specified credentials

    :param unix_user: the existing UNIX user of the bot
    :param bot_email: the email address for the bot account
    :param bot_passwd: the password for the bot's email account
    :param dbdir: the directory where the bot's data will be stored. default: ~/.config/team-bot/email@example.org
    """

    git.config(
        key="rebase.autoStash",
        value="true",
    )
    clone_repo = git.repo(
        name="Pull the team-bot repository",
        src="https://github.com/deltachat-bot/group-editor-bot",
        dest=f"/home/{unix_user}/group-editor-bot",
        rebase=True,
        _su_user=unix_user,
        _use_su_login=True,
    )

    if clone_repo.changed:
        server.shell(
            name="Compile group-editor-bot",
            commands=[
                "python3 -m venv ~/.local/lib/group-editor-bot.venv",
                "~/.local/lib/group-editor-bot.venv/bin/pip install -U pip wheel",
                f"cd /home/{unix_user}/group-editor-bot && ~/.local/lib/group-editor-bot.venv/bin/pip install .",
            ],
            _su_user=unix_user,
            _use_su_login=True,
        )

    if not dbdir:
        dbdir = f"/home/{unix_user}/.config/team_bot/{bot_email}/"
    secrets = [
        "DEBUG=true",
        f"TEAMS_DBDIR={dbdir}",
        f"TEAMS_INIT_EMAIL={bot_email}",
        f"TEAMS_INIT_PASSWORD={bot_passwd}",
    ]
    env = "\n".join(secrets)
    files.put(
        name="upload secrets",
        src=StringIO(env),
        dest=f"/home/{unix_user}/.env",
        mode="0600",
        user=unix_user,
    )

    files.directory(
        name="chown database directory",
        path=dbdir,
        mode="0700",
        recursive=True,
        user=unix_user,
    )

    files.template(
        name="upload group-editor-bot systemd unit",
        src=importlib.resources.files(__package__)
        / "pyinfra_assets"
        / "group-editor-bot.service.j2",
        dest=f"/home/{unix_user}/.config/systemd/user/group-editor-bot.service",
        user=unix_user,
        unix_user=unix_user,
        bot_email=bot_email,
        dbdir=dbdir,
    )

    systemd.daemon_reload(
        name=f"{unix_user}: load group-editor-bot systemd service",
        user_name=unix_user,
        user_mode=True,
        _su_user=unix_user,
        _use_su_login=True,
    )

    server.shell(
        name=f"enable {unix_user}'s systemd units to auto-start at boot",
        commands=[f"loginctl enable-linger {unix_user}"],
    )

    systemd.service(
        name=f"{unix_user}: restart group-editor-bot systemd service",
        service="group-editor-bot.service",
        running=True,
        restarted=True,
        user_mode=True,
        _su_user=unix_user,
        _use_su_login=True,
    )

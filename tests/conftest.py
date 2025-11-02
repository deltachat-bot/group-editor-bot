import os

import pytest

from group_editor_bot.hooks import hooks


@pytest.fixture
def bot(acfactory, log):
    assert os.getenv("CHATMAIL_DOMAIN")
    log.step("Configuring Bot")
    bot = acfactory.new_configured_bot()
    bot.account.set_config("displayname", "Bot from groupedit test")
    bot.add_hooks(hooks)
    bot.account.bring_online()
    return bot


@pytest.fixture
def group(acfactory, bot, log):
    log.step("Configuring Creator")
    creator = acfactory.get_online_account()
    creator.set_config("displayname", "Creator from groupedit test")

    log.step("Creator creates group")
    creator_group = creator.create_group("test_member_added")
    creator_invite = creator_group.get_qr_code()

    log.step("Bot joins group")
    bot_group = bot.account.secure_join(creator_invite)
    bot.account.wait_for_securejoin_joiner_success()
    bot.account.wait_for_incoming_msg()

    creator_group.creator = creator
    creator_group.bot_group = bot_group
    return creator_group


@pytest.fixture
def joiner(acfactory, log):
    def join_chat(chat):
        invite = chat.get_qr_code()
        joiner.secure_join(invite)
        joiner.wait_for_securejoin_joiner_success()
        log.step("Joiner receives member_added message")
        joiner.wait_for_incoming_msg()

    log.step("Configuring Joiner")
    joiner = acfactory.get_online_account()
    joiner.set_config("displayname", "Joiner from groupedit test")
    joiner.join_chat = join_chat
    return joiner

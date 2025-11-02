import os
import logging

import pytest
from deltachat_rpc_client.events import MemberListChanged

from group_editor_bot.hooks import delete_data, member_added_or_removed


def test_delete_data(acfactory):
    if not os.getenv("CHATMAIL_DOMAIN"):
        os.environ["CHATMAIL_DOMAIN"] = "nine.testrun.org"
    bot, user = acfactory.get_online_accounts(2)  # waiter lock
    joincode = bot.get_qr_code()
    chat = user.secure_join(joincode)
    bot.wait_for_securejoin_inviter_success()

    chat.send_text("hi :)")
    msg = bot.wait_for_incoming_msg()

    assert len(bot.get_chatlist()) == 3
    delete_data(msg.get_snapshot().chat)
    assert bot.get_contacts() == []
    assert len(bot.get_chatlist()) == 2


@pytest.mark.parametrize(
    ["text", "file", "reply_text", "reply_file"], [["", "", "", ""]]
)
def test_commands(text, file, reply_text, reply_file):
    pytest.skip("Not yet tested")


def test_member_added(acfactory, log):
    log.step("Configuring Bot")
    bot = acfactory.new_configured_bot()
    bot.logger = logging
    bot.add_hook(member_added_or_removed, MemberListChanged)
    bot.account.bring_online()

    log.step("Configuring Creator and Joiner")
    creator, joiner = acfactory.get_online_accounts(2)

    log.step("Creator creates group")
    creator_group = creator.create_group("test_member_added")
    invite = creator_group.get_qr_code()

    log.step("Bot joins group")
    bot_group = bot.account.secure_join(invite)
    bot.account.wait_for_securejoin_joiner_success()
    member_added_msg = bot.account.wait_for_incoming_msg()

    log.step("Bot sends test message")
    msg = bot_group.send_text("Bot sends test message")

    log.step("Creator receives test message")
    creator_msg = creator.wait_for_incoming_msg()
    assert creator_msg.get_snapshot().text == msg.get_snapshot().text

    log.step("Joiner joins group")
    joiner.secure_join(invite)
    joiner.wait_for_securejoin_joiner_success()

    log.step("Joiner receives re-sent message")
    member_added_msg = joiner.wait_for_incoming_msg()
    bot._process_messages()
    joiner_msg = joiner.wait_for_incoming_msg()
    assert joiner_msg.get_snapshot().text == msg.get_snapshot().text


def test_bot_removed(acfactory):
    pytest.skip("Not yet tested")


def tests_bot_adds_member(acfactory):
    pytest.skip("Not yet tested")

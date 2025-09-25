import os

import pytest

from group_editor_bot.hooks import delete_data


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


def test_member_added(acfactory):
    pytest.skip("Not yet tested")


def test_bot_removed(acfactory):
    pytest.skip("Not yet tested")


def tests_bot_adds_member(acfactory):
    pytest.skip("Not yet tested")

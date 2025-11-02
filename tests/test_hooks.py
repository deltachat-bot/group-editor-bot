import pytest
from deltachat_rpc_client.events import EventType

from group_editor_bot.hooks import delete_data


def test_delete_data(acfactory):
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


def test_member_added(bot, group, joiner, log):
    log.step("Bot sends test message")
    msg = group.bot_group.send_text("Bot sends test message")

    log.step("Creator receives test message")
    creator_msg = group.creator.wait_for_incoming_msg()
    assert creator_msg.get_snapshot().text == msg.get_snapshot().text

    log.step("Joiner joins group")
    joiner.join_chat(group)

    log.step("Joiner receives re-sent message")
    bot._process_messages()
    joiner_msg = joiner.wait_for_incoming_msg()
    assert joiner_msg.get_snapshot().text == msg.get_snapshot().text


def test_bot_forgets_non_commands(bot, group, log):
    log.step("Creator sends message to be forgotten immediately")
    group.send_text("Sensitive message")

    log.step("Bot forgets message immediately")
    msg = bot.account.wait_for_incoming_msg()
    bot._process_messages()
    assert msg not in group.bot_group.get_messages()


def test_bot_removed(bot, group, log):
    log.step("Creator removes Bot from Group")
    assert len(bot.account.get_chatlist()) == 1
    bot_contact = group.get_contacts()[0]
    group.remove_contact(bot_contact)

    def bot_removed(event):
        if event.kind == EventType.CHAT_MODIFIED:
            return True

    log.step("Bot gets removed")
    bot.run_until(bot_removed)
    assert bot.account.get_contacts() == []
    assert len(bot.account.get_chatlist()) == 0


def tests_bot_adds_member(bot, group, joiner, log):
    log.step("Bot sends test message")
    msg = group.bot_group.send_text("Bot sends test message")

    log.step("Creator receives test message")
    creator_msg = group.creator.wait_for_incoming_msg()
    assert creator_msg.get_snapshot().text == msg.get_snapshot().text

    log.step("Joiner joins group")
    joiner.join_chat(group.bot_group)

    def joiner_joined(event):
        if event.kind == EventType.SECUREJOIN_INVITER_PROGRESS:
            return True

    log.step("Joiner receives re-sent message")
    bot.run_until(joiner_joined)
    joiner_msg = joiner.wait_for_incoming_msg()
    assert joiner_msg.get_snapshot().text == msg.get_snapshot().text

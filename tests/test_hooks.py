import filecmp
import importlib.resources

import pytest
from deltachat_rpc_client.events import EventType

from group_editor_bot.hooks import HELP_MSG, delete_data


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
    ["text", "file", "r_text", "r_file", "resend"],
    [
        ("/help", None, HELP_MSG, None, False),
        ("/invite", None, "https://i.delta.chat", None, False),
        ("/pin", "hooks.py", "", "hooks.py", True),
        ("/pin test", "hooks.py", "test", "hooks.py", True),
        ("/editor test", None, "test", "durian-realtime-editor-v4.0.4.xdc", True),
        ("/editor", None, "", "durian-realtime-editor-v4.0.4.xdc", True),
    ],
)
def test_commands(bot, group, joiner, log, text, file, r_text, r_file, resend):
    filename = (
        str(importlib.resources.files("group_editor_bot") / file) if file else None
    )
    r_filename = (
        importlib.resources.files("group_editor_bot") / r_file if r_file else None
    )
    group.send_message(text=text, file=filename)
    log.step(f"Creator sent {text}")

    bot.account.wait_for_incoming_msg()
    bot._process_messages()

    reply = group.creator.wait_for_incoming_msg()
    log.step(f"Creator received {reply.get_snapshot().text}")
    assert reply.get_snapshot().text.startswith(r_text)
    if reply.get_snapshot().file:
        assert filecmp.cmp(reply.get_snapshot().file, r_filename)

    log.step("Joiner joins the group")
    joiner.join_chat(group)
    bot.account.wait_for_incoming_msg()
    bot._process_messages()

    if resend:
        log.step("Joiner listens for message...")
        resent = joiner.wait_for_incoming_msg()
        log.step("Joiner received message.")
        assert resent.get_snapshot().text.startswith(r_text)
        if resent.get_snapshot().file:
            assert filecmp.cmp(resent.get_snapshot().file, r_filename)


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


def test_bot_removed(bot, group, joiner, log):
    log.step("Joiner adds Bot to extra group")
    extra_group = joiner.create_group("groupedit test")
    extra_invite = extra_group.get_qr_code()

    log.step("Bot joins extra group")
    bot_extra_group = bot.account.secure_join(extra_invite)
    bot.account.wait_for_securejoin_joiner_success()
    bot.account.wait_for_incoming_msg()
    extra_contacts = bot_extra_group.get_contacts()

    log.step("Creator removes Bot from group")
    assert len(bot.account.get_chatlist()) == 2
    bot_contact = group.get_contacts()[0]
    group.remove_contact(bot_contact)

    def contacts_removed(event):
        if len(event.account.get_contacts()) == 1:
            return True

    log.step("Bot gets removed")
    bot.run_until(contacts_removed)
    assert bot.account.get_contacts()[0] == extra_contacts[0]
    assert len(bot.account.get_chatlist()) == 1
    assert bot_extra_group.get_full_snapshot().self_in_group


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

import importlib.resources
import os

from deltachat_rpc_client import Chat, EventType, events, run_bot_cli

hooks = events.HookCollection()

HELP_MSG = (
    "I am a bot that manages editors in groups.\n\n"
    "To create a new shared editor for the group, you can write:\n\n"
    "/editor Shopping List for Friday's Example Party\n\n"
    "I will send an editor to the group, which anyone can edit; and if new members are added, they will see it, too."
)


@hooks.on(events.NewMessage)
def command(event):
    snapshot = event.message_snapshot
    account = snapshot.chat.account

    if not snapshot.text.startswith("/"):
        """Not a command"""
    elif snapshot.text.strip() == "/invite":
        reply = snapshot.chat.send_text(snapshot.chat.get_qr_code())
    elif snapshot.text.strip() == "/help":
        reply = snapshot.chat.send_text(HELP_MSG)
    elif snapshot.text.startswith("/pin"):
        snapshot.chat.send_message(text=snapshot.text[5:], file=snapshot.file)
    elif snapshot.text.startswith("/editor"):
        editor_path = str(
            importlib.resources.files(__package__) / "durian-realtime-editor-v4.0.4.xdc"
        )
        snapshot.chat.send_message(text=snapshot.text[8:], file=editor_path)

    if snapshot.sender != account.self_contact:
        account.delete_messages([snapshot])
        print(f"Deleted message {snapshot.id}")
    if "reply" in locals():
        reply.wait_until_delivered()
        account.delete_messages([reply])


@hooks.on(events.MemberListChanged)
def member_added_or_removed(event):
    """If a member was added to the group chat, re-send own messages."""
    snapshot = event.message_snapshot
    if os.getenv("DEBUG") == "true":
        change = "added" if event.member_added else "removed"
        print("member %s was %s" % (event.member, change))
    if event.member_added:
        # If member added to group, resend pads
        resend_messages(snapshot.chat)
    else:
        if not snapshot.chat.get_full_snapshot().self_in_group:
            delete_data(snapshot.chat)


@hooks.on(events.RawEvent)
def catch_events(event):
    """This is called on every raw event and can be used for any kind of event handling.
    Unfortunately deltachat-rpc-client doesn't offer high-level events for MSG_DELIVERED or SECUREJOIN_INVITER_PROGRESS
    yet, so this needs to be done with raw events.

    :param event: the event object
    """
    if os.getenv("DEBUG") == "true":
        print(event)
    if event.kind == EventType.SECUREJOIN_INVITER_PROGRESS:
        if event.progress == 1000:
            resend_messages(event.account.get_chat_by_id(event.chat_id))
    if event.kind == EventType.IMAP_CONNECTED:
        event.account.set_config("selfstatus", HELP_MSG)
        event.account.set_config("delete_device_after", "0")
        print(
            "The bot can be reached via this invite link: "
            + event.account.get_qr_code()
        )


def resend_messages(chat: Chat):
    """Resend all own messages (except info messages) in a Chat."""
    to_resend = []
    for msg in chat.get_messages():
        msg_snap = msg.get_snapshot()
        if msg_snap.sender == chat.account.self_contact and not msg_snap.is_info:
            to_resend.append(msg)
    chat.resend_messages(to_resend)


def delete_data(chat: Chat):
    """For a message, delete the chat and all contacts which were in it to clean up."""
    contacts = chat.get_contacts()
    chat.delete()
    for member in contacts:
        member.delete()


def main():
    """This is the CLI entry point."""
    run_bot_cli(hooks)


if __name__ == "__main__":
    main()

import importlib.resources
import os

from deltachat_rpc_client import EventType, Chat, events, run_bot_cli

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

    if not snapshot.text.startswith("/"):
        return  # Not a command
    elif snapshot.text == "/invite":
        snapshot.chat.send_text(snapshot.chat.get_qr_code())
    elif snapshot.text.strip() == "/help":
        snapshot.chat.send_text(HELP_MSG)
    elif snapshot.text == "/pin":
        snapshot.chat.send_message(text=snapshot.text[5:], file=snapshot.file)
    elif snapshot.text == "/editor":
        editor_path = (
            importlib.resources.files(__package__) / "durian-realtime-editor-v4.0.4.xdc"
        )
        snapshot.chat.send_message(text=snapshot.text[8:], file=editor_path)

    if snapshot.sender != event.account.self_contact:
        event.account.delete_messages([snapshot])
        print(f"Deleted message {snapshot.id}")


@hooks.on(events.MemberListChanged)
def member_added_or_removed(event):
    """If a member was added to the group chat, re-send own messages."""
    if event.member_added:
        # If member added to group, resend pads
        to_resend = []
        for msg in event.chat:
            if msg.sender == event.account.self_contact:
                to_resend.append(msg)
        event.chat.resend_messages(to_resend)
    else:
        if event.member == event.account.self_contact:
            delete_data(event.chat)




@hooks.on(events.RawEvent)
def catch_events(event):
    """This is called on every raw event and can be used for any kind of event handling.
    Unfortunately deltachat-rpc-client doesn't offer high-level events for MSG_DELIVERED or SECUREJOIN_INVITER_PROGRESS
    yet, so this needs to be done with raw events.

    :param event: the event object
    """
    if os.getenv("DEBUG").lower() == "true":
        print(event)
    if event.kind == EventType.IMAP_CONNECTED:
        event.account.set_config("selfstatus", HELP_MSG)
        event.account.set_config("delete_device_after", "3600")
        print(
            "The bot can be reached via this invite link: "
            + event.account.get_qr_code()
        )


def delete_data(chat: Chat):
    """For a message, delete the chat and all contacts which were in it to clean up.

    :param msg: a Delta Chat Message snapshot
    """
    contacts = chat.get_contacts()
    chat.delete()
    for member in contacts:
        member.delete()


def main():
    """This is the CLI entry point."""
    run_bot_cli(hooks)


if __name__ == "__main__":
    main()

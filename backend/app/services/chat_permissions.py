"""Simplified group and channel role checks for Reyno Messenger Lite.

Groups and channels do not expose complex permission matrices; they only
distinguish between 'owner', 'admin', and 'member'.
"""


def is_admin_or_owner(member) -> bool:
    return bool(member and not member.is_deleted and member.role in ('owner', 'admin'))


def ensure_can_send(chat, member, message_type='text', has_media=False):
    if not member or member.is_deleted:
        return 'You are not a member of this chat.'

    if chat.chat_type == 'channel':
        if not is_admin_or_owner(member):
            return 'Only channel admins can post messages.'

    return None


def can_manage_members(chat, member) -> bool:
    if not member or member.is_deleted:
        return False
    return is_admin_or_owner(member)


def can_promote_admins(chat, member) -> bool:
    if not member or member.is_deleted:
        return False
    return is_admin_or_owner(member)


def can_delete_message_for_all(chat, member, message, user_id: str) -> bool:
    """Disabled in Lite: deletion is one-sided only ("delete for me").

    Kept as a function so old callers fail closed (always False) instead of
    accidentally re-enabling two-way deletion.
    """
    return False


def can_pin_in_chat(chat, member) -> bool:
    if not member or member.is_deleted:
        return False
    if chat.chat_type == 'private':
        return True
    return is_admin_or_owner(member)

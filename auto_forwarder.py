# ----------------------------------------------------------------------------------
# Message Forwarder Plugin for exteraGram
# Copyright (C) 2025 @T3SL4
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------
#
# DISCLAIMER:
# This plugin automates actions on a user's personal Telegram account ("self-botting").
# It is intended for educational and personal automation purposes only. Misuse may
# violate Telegram's Terms of Service and can lead to account limitations or bans.
# The author assumes no liability for any consequences arising from its use.
# USE ENTIRELY AT YOUR OWN RISK.
#
# ----------------------------------------------------------------------------------

# --- Standard Library Imports ---
import json
import traceback
import random
import collections
import time
import re
import os
import threading

# --- Chaquopy Import for Java Interoperability ---
from java.chaquopy import dynamic_proxy

# --- Base Plugin and UI Imports ---
from base_plugin import BasePlugin, MenuItemData, MenuItemType
from ui.settings import Header, Text, Divider, Input
from ui.alert import AlertDialogBuilder
from ui.bulletin import BulletinHelper

# --- Android & Chaquopy Imports ---
from android_utils import log, run_on_ui_thread
from android.widget import EditText, FrameLayout, CheckBox, LinearLayout, TextView, Toast, ScrollView
from android.text import InputType, Html
from android.text.method import LinkMovementMethod
from android.util import TypedValue
from android.view import View, ViewGroup
from java.util import ArrayList, HashSet, Scanner
from android.content.res import ColorStateList
from android.content import ClipData, ClipboardManager, Context
from android.os import Handler, Looper
from java.lang import Runnable, String as JavaString
from android.content import Intent
from android.net import Uri
from android.graphics import Typeface
from java.net import URL, HttpURLConnection
from java.io import File, FileOutputStream

# --- Telegram & Client Utilities ---
from org.telegram.messenger import NotificationCenter, MessageObject, R, Utilities
from org.telegram.tgnet import TLRPC
from org.telegram.ui.ActionBar import Theme
from com.exteragram.messenger.plugins.ui import PluginSettingsActivity
from com.exteragram.messenger.plugins import PluginsController
from client_utils import (
    get_messages_controller,
    get_last_fragment,
    get_account_instance,
    send_request,
    RequestCallback,
    get_user_config
)

# --- Plugin Metadata ---
__id__ = "auto_forwarder"
__name__ = "Auto Forwarder"
__description__ = "Sets up forwarding rules for any chat, including users, groups, and channels."
__author__ = "@T3SL4"
__version__ = "1.6.5"
__min_version__ = "11.9.1"
__icon__ = "Putin_1337/14"

# --- Constants & Default Settings ---
FORWARDING_RULES_KEY = "forwarding_rules_v1337"
DEFAULT_SETTINGS = {
    "deferral_timeout_ms": 5000,
    "min_msg_length": 1,
    "max_msg_length": 4096,
    "deduplication_window_seconds": 10.0,
    "album_timeout_ms": 800,
    "antispam_delay_seconds": 1.0
}
FILTER_TYPES = {
    "text": "Text Messages",
    "photos": "Photos",
    "videos": "Videos",
    "documents": "Files / Documents",
    "audio": "Audio Files",
    "voice": "Voice Messages",
    "video_messages": "Video Messages (Roundies)",
    "stickers": "Stickers",
    "gifs": "GIFs & Animations"
}
FAQ_TEXT = """--- **Disclaimer and Responsible Usage** ---
Please be aware that using a plugin like this automates actions on your personal Telegram account. This practice is often referred to as 'self-botting'.
This kind of automation may be considered a violation of [Telegram's Terms of Service](https://telegram.org/tos), which can prohibit bot-like activity from user accounts.
Using this plugin carries potential risks, including account limitations or bans. You accept full responsibility for your actions. The author is not responsible for any consequences from your use or misuse of this tool.
**Use at your own risk.**

--- **FAQ** ---
**🚀 Core Functionality**
* **How do I create a rule?**
Go into any chat you want to forward messages *from*. Tap the three-dots menu (⋮) in the top right and select "Auto Forward...". A dialog will then ask for the destination chat.
* **How do I edit or delete a rule?**
Go to a chat where a rule is active and open the "Auto Forward..." menu item again. A "Manage Rule" dialog will appear, allowing you to modify or delete it. You can also manage all rules from the main plugin settings page.
* **What's the difference between "Copy" and "Forward" mode?**
When setting up a rule, you have a checkbox for "Remove Original Author".
- **Checked (Copy Mode):** Sends a brand new message to the destination. It looks like you sent it yourself. All text formatting is preserved.
- **Unchecked (Forward Mode):** Performs a standard Telegram forward, including the "Forwarded from..." header, preserving the original author's context.
* **Can I control which messages get forwarded?**
Yes. When creating or modifying a rule, you can choose to forward messages from regular users, bots, and your own outgoing messages independently.

--- **✨ Advanced Features & Formatting** ---
* **How does the Anti-Spam Firewall work?**
It's a rate-limiter that prevents a single user from flooding your destination chat. It works by enforcing a minimum time delay between forwards *from the same person*. You can configure this delay in the General Settings.
* **How do the content filters work?**
When creating or modifying a rule, you'll see checkboxes for different message types (Text, Photos, Videos, etc.). Simply uncheck any content type you *don't* want to be forwarded for that specific rule. For example, you can set up a rule to forward only photos and videos from a channel, ignoring all text messages.
* **How does keyword/regex filtering work?**
You can specify keywords or regex patterns that messages must contain to be forwarded. This works for text messages and media captions:
- **Keywords:** Simple text matching (case-insensitive). Example: `"bitcoin"` will match messages containing "Bitcoin", "BITCOIN", etc.
- **Regex Patterns:** Advanced pattern matching. Example: `"\\\\b(btc|bitcoin|₿)\\\\b"` will match whole words containing btc, bitcoin, or the bitcoin symbol.
- **Leave the field empty** to disable keyword filtering (forward all messages that pass other filters).
- If a regex pattern fails to compile, it will fall back to simple case-insensitive text matching.
* **Does the plugin support text formatting (Markdown)?**
Yes, completely. In 'Copy' mode, the plugin perfectly preserves all text formatting from the original message. This includes:
- **Bold** and *italic* text
- `Monospace code`
- ~~Strikethrough~~ and __underline__
- ||Spoilers||
- [Custom Hyperlinks](https://telegram.org)
- Mentions and #hashtags

--- **⚙️ Technical Settings & Troubleshooting** ---
* **What do the General Settings mean?**
- **Min/Max Message Length:** Filters *text messages* based on their character count.
- **Media Deferral Timeout:** A safety net for media files. When a file arrives, your app might need a moment to get the data required for forwarding. This is how long the plugin waits. Increase this value if large files you receive sometimes fail to forward.
- **Album Buffering Timeout:** When a gallery of photos/videos is sent, the plugin waits a brief moment to collect all the images before forwarding them together as a single album. This controls that waiting period.
- **Deduplication Window:** Prevents double-forwards. If Telegram sends a duplicate notification for the same message within this time window (in seconds), the plugin will ignore it.
- **Anti-Spam Delay:** The core setting for the firewall, as explained above. Set to `0` to disable it.
* **Why do large files I send myself sometimes fail to forward?**
This is a known limitation. If your file takes longer to upload than the "Media Deferral Timeout", the plugin may not be able to forward it. The feature is most reliable for forwarding messages you receive or for your own small files that upload instantly.
"""

class DeferredTask(dynamic_proxy(Runnable)):
    """A robust Runnable class to handle the timeout for deferred messages."""
    def __init__(self, plugin, event_key):
        super().__init__()
        self.plugin = plugin
        self.event_key = event_key

    def run(self):
        """This method is called by the Android Handler after the timeout to re-process a message."""
        self.plugin._process_timed_out_message(self.event_key)


class AlbumTask(dynamic_proxy(Runnable)):
    """A Runnable class to handle the timeout for album processing."""
    def __init__(self, plugin, grouped_id):
        super().__init__()
        self.plugin = plugin
        self.grouped_id = grouped_id

    def run(self):
        """This method is called by the Android Handler after the album timeout to process the buffered album."""
        self.plugin._process_album(self.grouped_id)


class AutoForwarderPlugin(dynamic_proxy(NotificationCenter.NotificationCenterDelegate), BasePlugin):
    """
    The main class for the Auto Forwarder plugin. It handles forwarding rules,
    listens for new messages, and manages the complex logic for forwarding
    different types of content correctly.
    """
    TON_ADDRESS = "UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm"
    USDT_ADDRESS = "TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo"
    USER_TIMESTAMP_CACHE_SIZE = 500

    # --- Updater Configuration ---
    GITHUB_OWNER = "0x11DFE"
    GITHUB_REPO = "Auto-Forwarder-Plugin"
    UPDATE_INTERVAL_SECONDS = 6 * 60 * 60  # 6 hours

    class InstallCallback(dynamic_proxy(Utilities.Callback)):
        """A robust proxy class for the plugin installation callback."""
        def __init__(self, callback_func):
            super().__init__()
            self.callback_func = callback_func
        
        def run(self, arg):
            try:
                self.callback_func(arg)
            except Exception:
                log(f"[{__id__}] Error in install callback proxy: {traceback.format_exc()}")

    def __init__(self):
        super().__init__()
        self.id = __id__
        self.forwarding_rules = {}
        self.error_message = None
        self.deferred_messages = {}
        self.album_buffer = {}
        self.processed_keys = collections.deque(maxlen=200)
        self.handler = Handler(Looper.getMainLooper())
        self.user_last_message_time = collections.OrderedDict()
        self.updater_thread = None
        self.stop_updater_thread = threading.Event()
        self._load_configurable_settings()

    def on_plugin_load(self):
        """Called when the plugin is loaded. Registers the new message observer and starts the updater."""
        log(f"[{self.id}] Loading version {__version__}...")
        self._load_configurable_settings()
        self._load_forwarding_rules()
        self._add_chat_menu_item()
        self.stop_updater_thread.clear()
        if self.updater_thread is None or not self.updater_thread.is_alive():
            self.updater_thread = threading.Thread(target=self._updater_loop)
            self.updater_thread.daemon = True
            self.updater_thread.start()
            log(f"[{self.id}] Auto-updater thread started.")

        def register_observer():
            account_instance = get_account_instance()
            if account_instance:
                account_instance.getNotificationCenter().addObserver(self, NotificationCenter.didReceiveNewMessages)
                log(f"[{self.id}] Message observer successfully registered.")

        run_on_ui_thread(register_observer)

    def on_plugin_unload(self):
        """Called when the plugin is unloaded. Removes the observer and cancels any pending tasks."""
        self.stop_updater_thread.set()
        log(f"[{self.id}] Auto-updater thread stopped.")

        def unregister_observer():
            account_instance = get_account_instance()
            if account_instance:
                account_instance.getNotificationCenter().removeObserver(self, NotificationCenter.didReceiveNewMessages)
                log(f"[{self.id}] Message observer successfully removed.")

        run_on_ui_thread(unregister_observer)
        self.handler.removeCallbacksAndMessages(None)

    def _load_configurable_settings(self):
        """Loads all configurable settings from storage into instance attributes."""
        log(f"[{self.id}] Reloading configurable settings into memory.")
        self.min_msg_length = int(self.get_setting("min_msg_length", str(DEFAULT_SETTINGS["min_msg_length"])))
        self.max_msg_length = int(self.get_setting("max_msg_length", str(DEFAULT_SETTINGS["max_msg_length"])))
        self.deferral_timeout_ms = int(self.get_setting("deferral_timeout_ms", str(DEFAULT_SETTINGS["deferral_timeout_ms"])))
        self.album_timeout_ms = int(self.get_setting("album_timeout_ms", str(DEFAULT_SETTINGS["album_timeout_ms"])))
        self.deduplication_window_seconds = float(self.get_setting("deduplication_window_seconds", str(DEFAULT_SETTINGS["deduplication_window_seconds"])))
        self.antispam_delay_seconds = float(self.get_setting("antispam_delay_seconds", str(DEFAULT_SETTINGS["antispam_delay_seconds"])))

    def _is_media_complete(self, message):
        """Checks if a media message has a file_reference, which is needed for forwarding."""
        if not message or not hasattr(message, 'media') or not message.media:
            return True
        if hasattr(message.media, 'photo') and getattr(message.media.photo, 'file_reference', None):
            return True
        if hasattr(message.media, 'document') and getattr(message.media.document, 'file_reference', None):
            return True
        return False

    def didReceivedNotification(self, id, account, args):
        """The main entry point, called by Telegram for every new message event."""
        if id != NotificationCenter.didReceiveNewMessages:
            return
        try:
            if not self.forwarding_rules:
                return
            messages_list = args[1]
            for i in range(messages_list.size()):
                message_object = messages_list.get(i)
                if not (hasattr(message_object, 'messageOwner') and message_object.messageOwner):
                    continue
                self.handle_message_event(message_object)
        except Exception:
            log(f"[{self.id}] ERROR in notification handler: {traceback.format_exc()}")

    def _get_author_type(self, message):
        """Determines if the message is from a user, a bot, or is outgoing."""
        if message.out:
            return "outgoing"
        
        author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
        if author_entity and getattr(author_entity, 'bot', False):
            return "bot"
        
        return "user"

    def handle_message_event(self, message_object):
        """Main processing pipeline for each incoming message."""
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule or not rule.get("enabled", False):
            return

        author_type = self._get_author_type(message)
        if author_type == "outgoing" and not rule.get("forward_outgoing", True):
            return
        if author_type == "user" and not rule.get("forward_users", True):
            return
        if author_type == "bot" and not rule.get("forward_bots", True):
            return

        grouped_id = getattr(message, 'grouped_id', 0)
        if grouped_id != 0:
            if grouped_id not in self.album_buffer:
                log(f"[{self.id}] Detected start of new album: {grouped_id}")
                album_task = AlbumTask(self, grouped_id)
                self.album_buffer[grouped_id] = {'messages': [], 'task': album_task}
                self.handler.postDelayed(album_task, self.album_timeout_ms)
            self.album_buffer[grouped_id]['messages'].append(message_object)
            return

        if self.antispam_delay_seconds > 0:
            author_id = get_user_config().getClientUserId() if message.out else self._get_id_from_peer(message.from_id)
            if author_id:
                current_time = time.time()
                last_time = self.user_last_message_time.get(author_id)
                if last_time and (current_time - last_time) < self.antispam_delay_seconds:
                    log(f"[{self.id}] Dropping message from user {author_id} due to anti-spam rate limit.")
                    return
                self.user_last_message_time[author_id] = current_time
                if len(self.user_last_message_time) > self.USER_TIMESTAMP_CACHE_SIZE:
                    self.user_last_message_time.popitem(last=False)

        event_key = None
        if message.out:
            event_key = ("outgoing", message.dialog_id, message.date, message.message or "")
        else:
            author_id = self._get_id_from_peer(message.from_id)
            event_key = ("incoming", author_id, source_chat_id, message.id)

        if any(key == event_key for key, ts in self.processed_keys):
            return

        is_media = hasattr(message, 'media') and message.media and not isinstance(message.media, TLRPC.TL_messageMediaEmpty)
        is_incomplete_media = is_media and not self._is_media_complete(message)
        is_reply = hasattr(message, 'reply_to') and message.reply_to is not None
        is_reply_object_missing = is_reply and not (hasattr(message_object, 'replyMessageObject') and message_object.replyMessageObject)
        if is_incomplete_media or is_reply_object_missing:
            if event_key not in self.deferred_messages:
                reason = "incomplete media" if is_incomplete_media else "missing reply object"
                log(f"[{self.id}] Deferring message due to {reason}. Key: {event_key}")
                deferred_task = DeferredTask(self, event_key)
                self.deferred_messages[event_key] = (message_object, deferred_task)
                self.handler.postDelayed(deferred_task, self.deferral_timeout_ms)
            return

        if event_key in self.deferred_messages:
            _, deferred_task = self.deferred_messages[event_key]
            self.handler.removeCallbacks(deferred_task)
            del self.deferred_messages[event_key]
        
        self._process_and_send(message_object, event_key)

    def _process_timed_out_message(self, event_key):
        """Processes a deferred message, re-fetching it from cache to ensure data is fresh."""
        if event_key in self.deferred_messages:
            log(f"[{self.id}] Processing deferred message after timeout. Key: {event_key}")
            message_object, _ = self.deferred_messages[event_key]
            final_message_object = message_object
            try:
                original_message = message_object.messageOwner
                if not original_message.out and hasattr(get_messages_controller(), 'getMessage'):
                    cached_message_obj = get_messages_controller().getMessage(original_message.dialog_id, original_message.id)
                    if cached_message_obj:
                        final_message_object = cached_message_obj
                        log(f"[{self.id}] Successfully re-fetched message from cache.")
            except Exception as e:
                log(f"[{self.id}] Could not re-fetch message from cache, proceeding with original object. Error: {e}")
            self._process_and_send(final_message_object, event_key)
            del self.deferred_messages[event_key]

    def _process_album(self, grouped_id):
        """Processes a buffered album after the timeout."""
        log(f"[{self.id}] Processing album {grouped_id} after timeout.")
        album_data = self.album_buffer.pop(grouped_id, None)
        if not album_data or not album_data['messages']:
            return
        
        first_message_obj = album_data['messages'][0]
        first_message = first_message_obj.messageOwner
        source_chat_id = self._get_id_from_peer(first_message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule:
            return

        album_key = (self._get_id_from_peer(first_message.from_id), source_chat_id, grouped_id)
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == album_key for key, ts in self.processed_keys):
            return
        self.processed_keys.append((album_key, time.time()))
        self._send_album(album_data['messages'], rule)

    def _is_message_allowed_by_filters(self, message_object, rule):
        """Checks if a message should be forwarded based on the rule's media filters."""
        filters = rule.get("filters", {})
        if not filters:
            return True
        if message_object.isPhoto(): return filters.get("photos", True)
        if message_object.isSticker(): return filters.get("stickers", True)
        if message_object.isVoice(): return filters.get("voice", True)
        if message_object.isRoundVideo(): return filters.get("video_messages", True)
        if message_object.isGif(): return filters.get("gifs", True)
        if message_object.isMusic(): return filters.get("audio", True)
        if message_object.isVideo(): return filters.get("videos", True)
        if message_object.isDocument(): return filters.get("documents", True)
        return filters.get("text", True)

    def _passes_keyword_filter(self, text_to_check, pattern):
        """Checks if text matches a keyword/regex pattern, with a fallback."""
        if not pattern:
            return True
        if not text_to_check:
            return False
        try:
            compiled_regex = re.compile(pattern, re.IGNORECASE)
            if compiled_regex.search(text_to_check):
                return True
        except re.error:
            if pattern.lower() in text_to_check.lower():
                return True
        return False

    def _process_and_send(self, message_object, event_key):
        """Final processing stage that applies all filters and sends the message."""
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == event_key for key, ts in self.processed_keys):
            return
        
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule:
            return

        if not self._is_message_allowed_by_filters(message_object, rule):
            return

        keyword_pattern = rule.get("keyword_pattern", "").strip()
        if keyword_pattern:
            text_to_check = message.message or ""
            if not self._passes_keyword_filter(text_to_check, keyword_pattern):
                return
        
        is_text_based = not message.media or isinstance(message.media, (TLRPC.TL_messageMediaEmpty, TLRPC.TL_messageMediaWebPage))
        if is_text_based:
            if not (self.min_msg_length <= len(message.message or "") <= self.max_msg_length):
                return

        self.processed_keys.append((event_key, time.time()))
        self._send_forwarded_message(message_object, rule)
    
    def _get_java_len(self, py_string: str) -> int:
        if not py_string:
            return 0
        return JavaString(py_string).length()

    def _add_user_entities(self, entities: ArrayList, text: str, user_entity: TLRPC.TL_user, display_name: str):
        if not all([entities is not None, text, user_entity, display_name]):
            return
        try:
            offset = text.rfind(display_name)
            if offset == -1: return

            length = self._get_java_len(display_name)
            
            url_entity = TLRPC.TL_messageEntityTextUrl()
            url_entity.url = f"tg://user?id={user_entity.id}"
            url_entity.offset, url_entity.length = offset, length
            entities.add(url_entity)

            bold_entity = TLRPC.TL_messageEntityBold()
            bold_entity.offset, bold_entity.length = offset, length
            entities.add(bold_entity)
        except Exception as e:
            log(f"[{self.id}] Failed to add user entities for {display_name}: {e}")

    def _build_reply_quote(self, message_object):
        replied_message_obj = message_object.replyMessageObject
        if not replied_message_obj or not replied_message_obj.messageOwner:
            return None, None
        
        replied_message = replied_message_obj.messageOwner
        author_id = self._get_id_from_peer(replied_message.from_id)
        author_entity = self._get_chat_entity(author_id)
        author_name = self._get_entity_name(author_entity)
        original_fwd_tag, _ = self._get_original_author_details(replied_message.fwd_from)

        quote_snippet = "Media"
        if replied_message_obj.isPhoto(): quote_snippet = "Photo"
        elif replied_message_obj.isVideo(): quote_snippet = "Video"
        elif replied_message_obj.isVoice(): quote_snippet = "Voice Message"
        elif replied_message_obj.isSticker(): quote_snippet = str(replied_message_obj.messageText) if replied_message_obj.messageText else "Sticker"
        elif replied_message and replied_message.message:
            raw_text = replied_message.message
            quote_snippet = re.sub(r'[\s\r\n]+', ' ', raw_text).strip()

        if self._get_java_len(quote_snippet) > 44:
            quote_snippet = quote_snippet[:44].strip() + "..."
                
        if original_fwd_tag:
            quote_snippet += f" (from {original_fwd_tag})"

        quote_text = f"{author_name}\n\u200b{quote_snippet}"
        entities = ArrayList()
        
        if isinstance(author_entity, TLRPC.TL_user):
            self._add_user_entities(entities, quote_text, author_entity, author_name)
        else:
            bold_entity = TLRPC.TL_messageEntityBold()
            bold_entity.offset, bold_entity.length = 0, self._get_java_len(author_name)
            entities.add(bold_entity)

        quote_entity = TLRPC.TL_messageEntityBlockquote()
        quote_entity.offset, quote_entity.length = 0, self._get_java_len(quote_text)
        entities.add(quote_entity)

        return quote_text, entities

    def _send_album(self, message_objects, rule):
        if not message_objects: return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})
        keyword_pattern = rule.get("keyword_pattern", "").strip()

        try:
            req = TLRPC.TL_messages_sendMultiMedia()
            req.peer = get_messages_controller().getInputPeer(to_peer_id)
            multi_media_list = ArrayList()

            album_caption = ""
            album_entities = None
            text_allowed = filters.get("text", True)
            if text_allowed:
                for msg_obj in message_objects:
                    if msg_obj.messageOwner and msg_obj.messageOwner.message:
                        album_caption = msg_obj.messageOwner.message
                        album_entities = msg_obj.messageOwner.entities
                        break

            if keyword_pattern and not self._passes_keyword_filter(album_caption, keyword_pattern):
                return

            first_message_obj = message_objects[0]
            first_message = first_message_obj.messageOwner
            
            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(first_message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(first_message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(first_message, source_entity, author_entity)
                    if header_text:
                        prefix_text += header_text
                    if header_entities:
                        prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(first_message_obj)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            header_attached = False
            for original_msg_obj in message_objects:
                current_msg_obj = original_msg_obj
                if not self._is_media_complete(original_msg_obj.messageOwner):
                    try:
                        original_message = original_msg_obj.messageOwner
                        if hasattr(get_messages_controller(), 'getMessage'):
                            cached_message_obj = get_messages_controller().getMessage(original_message.dialog_id, original_message.id)
                            if cached_message_obj and self._is_media_complete(cached_message_obj.messageOwner):
                                current_msg_obj = cached_message_obj
                    except Exception as e:
                        log(f"[{self.id}] Could not refresh album part from cache. Error: {e}")

                if not self._is_message_allowed_by_filters(current_msg_obj, rule):
                    continue
                
                input_media = self._get_input_media(current_msg_obj)
                if not input_media:
                    continue

                single_media = TLRPC.TL_inputSingleMedia()
                single_media.media = input_media
                single_media.random_id = random.getrandbits(63)

                if not header_attached:
                    final_caption = f"{prefix_text}\n\n{album_caption}".strip()
                    final_entities = self._prepare_final_entities(prefix_text, prefix_entities, album_entities)
                    single_media.message = final_caption
                    if final_entities and not final_entities.isEmpty():
                        single_media.entities = final_entities
                        single_media.flags |= 1
                    header_attached = True
                else:
                    single_media.message = ""
                multi_media_list.add(single_media)

            if not multi_media_list.isEmpty():
                req.multi_media = multi_media_list
                send_request(req, RequestCallback(lambda r, e: None))
        except Exception:
            log(f"[{self.id}] ERROR in _send_album: {traceback.format_exc()}")

    def _send_forwarded_message(self, message_object, rule):
        message = message_object.messageOwner
        if not message: return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})
        text_allowed = filters.get("text", True)

        try:
            input_media = self._get_input_media(message_object)
            original_text = (message.message or "") if text_allowed else ""
            original_entities = message.entities if text_allowed else None

            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(message, source_entity, author_entity)
                    if header_text: prefix_text += header_text
                    if header_entities: prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(message_object)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            message_text = f"{prefix_text}\n\n{original_text}".strip()
            entities = self._prepare_final_entities(prefix_text, prefix_entities, original_entities)

            req = None
            if input_media:
                req = TLRPC.TL_messages_sendMedia()
                req.media, req.message = input_media, message_text
            elif message_text.strip():
                req = TLRPC.TL_messages_sendMessage()
                req.message = message_text
            
            if req:
                req.peer = get_messages_controller().getInputPeer(to_peer_id)
                req.random_id = random.getrandbits(63)
                if entities and not entities.isEmpty():
                    req.entities = entities
                    req.flags |= 8
                send_request(req, RequestCallback(lambda r, e: None))
        except Exception:
            log(f"[{self.id}] ERROR in _send_forwarded_message: {traceback.format_exc()}")

    def _get_input_media(self, message_object):
        media = getattr(message_object.messageOwner, "media", None)
        if not media: return None
        try:
            if isinstance(media, TLRPC.TL_messageMediaPhoto) and hasattr(media, "photo"):
                photo = media.photo
                input_media = TLRPC.TL_inputMediaPhoto();
                input_media.id = TLRPC.TL_inputPhoto()
                input_media.id.id, input_media.id.access_hash = photo.id, photo.access_hash
                input_media.id.file_reference = photo.file_reference or bytearray(0)
                return input_media
            if isinstance(media, TLRPC.TL_messageMediaDocument) and hasattr(media, "document"):
                doc = media.document
                input_media = TLRPC.TL_inputMediaDocument();
                input_media.id = TLRPC.TL_inputDocument()
                input_media.id.id, input_media.id.access_hash = doc.id, doc.access_hash
                input_media.id.file_reference = doc.file_reference or bytearray(0)
                return input_media
        except Exception:
            log(f"[{self.id}] Failed to get input media: {traceback.format_exc()}")
        return None

    def create_settings(self) -> list:
        self._load_configurable_settings()
        self._load_forwarding_rules()
        settings_ui = [
            Header(text="General Settings"),
            Input(key="min_msg_length", text="Minimum Message Length", default=str(DEFAULT_SETTINGS["min_msg_length"]), subtext="For text-only messages."),
            Input(key="max_msg_length", text="Maximum Message Length", default=str(DEFAULT_SETTINGS["max_msg_length"]), subtext="For text-only messages."),
            Input(key="deferral_timeout_ms", text="Media Deferral Timeout (ms)", default=str(DEFAULT_SETTINGS["deferral_timeout_ms"]), subtext="Safety net for slow media downloads. Increase if files fail to send."),
            Input(key="album_timeout_ms", text="Album Buffering Timeout (ms)", default=str(DEFAULT_SETTINGS["album_timeout_ms"]), subtext="How long to wait for all media in an album before sending."),
            Input(key="deduplication_window_seconds", text="Deduplication Window (Seconds)", default=str(DEFAULT_SETTINGS["deduplication_window_seconds"]), subtext="Time window to ignore duplicate events."),
            Input(key="antispam_delay_seconds", text="Anti-Spam Delay (Seconds)", default=str(DEFAULT_SETTINGS["antispam_delay_seconds"]), subtext="Minimum time between forwards from the same user. 0 to disable."),
            Divider(),
            Header(text="Active Forwarding Rules")
        ]
        if not self.forwarding_rules:
            settings_ui.append(Text(text="No rules configured. Set one from any chat's menu.", icon="msg_info"))
        else:
            sorted_rules = sorted(self.forwarding_rules.items(), key=lambda item: self._get_chat_name(item[0]).lower())
            for source_id, rule_data in sorted_rules:
                source_name = self._get_chat_name(source_id)
                dest_name = self._get_chat_name(rule_data.get("destination", 0)) if rule_data.get("destination") else "Not Set"
                style = "(Copy)" if rule_data.get("drop_author", True) else "(Forward)"
                settings_ui.append(Text(
                    text=f"From: {source_name}\nTo: {dest_name} {style}",
                    icon="msg_edit",
                    on_click=lambda v, sid=source_id: self._show_rule_action_dialog(sid)
                ))
        settings_ui.append(Divider())
        settings_ui.extend([
            Divider(),
            Header(text="Support the Developer"),
            Text(text="TON", icon="msg_ton", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.TON_ADDRESS, "TON"))),
            Text(text="USDT (TRC20)", icon="msg_copy", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.USDT_ADDRESS, "USDT"))),
            Divider(),
            Text(text="Disclaimer & FAQ", icon="msg_help", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._show_faq_dialog())),
            Divider(),
            Text(
                text="Check for Updates",
                icon="msg_update",
                accent=True,
                on_click=lambda v: self.check_for_updates(is_manual=True)
            )
        ])
        return settings_ui
    
    def _process_changelog_markdown(self, text):
        """Processes release notes from GitHub into displayable HTML with proper spacing."""
        def process_inline(line):
            line = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', line)
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'__(.*?)__', r'<u>\1</u>', line)
            line = re.sub(r'~~(.*?)~~', r'<s>\1</s>', line)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            line = re.sub(r'`(.*?)`', r'<code>\1</code>', line)
            return line

        html_lines = []
        for line in text.replace('\r', '').split('\n'):
            stripped = line.strip()
            
            if not stripped:
                html_lines.append("")
                continue
            
            if stripped.startswith('### '):
                html_lines.append(f"<b>{process_inline(stripped[4:])}</b>")
            elif stripped.startswith('* '):
                html_lines.append(f"•&nbsp;&nbsp;{process_inline(stripped[2:])}")
            elif stripped.startswith('- '):
                html_lines.append(f"&nbsp;&nbsp;-&nbsp;&nbsp;{process_inline(stripped[2:])}")
            else:
                html_lines.append(process_inline(stripped))
        
        html_text = '<br>'.join(html_lines)
        return re.sub(r'(<br>\s*){2,}', '<br><br>', html_text)

    def _show_faq_dialog(self):
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Disclaimer & FAQ")
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))

            scroller = ScrollView(activity)
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 2)

            faq_text_view = TextView(activity)
            
            def process_inline_markdown(text):
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
                text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                text = re.sub(r'`(.*?)`', r'<tt>\1</tt>', text)
                return text

            accent_color_hex = f"#{Theme.getColor(Theme.key_dialogTextLink) & 0xFFFFFF:06x}"
            spoiler_color_hex = f"#{Theme.getColor(Theme.key_windowBackgroundGray) & 0xFFFFFF:06x}"
            
            html_lines = []
            source_lines = FAQ_TEXT.strip().split('\n')

            for i, line in enumerate(source_lines):
                stripped_line = line.strip()
                
                if not stripped_line:
                    html_lines.append("")
                    continue

                if stripped_line == '---':
                    html_lines.append(f"<p align='center'><font color='{accent_color_hex}'>•&nbsp;•&nbsp;•</font></p>")
                    continue
                
                content_spoilers_processed = re.sub(r'\|\|(.*?)\|\|', rf'<font style="background-color:{spoiler_color_hex};color:{spoiler_color_hex};">&nbsp;\1&nbsp;</font>', stripped_line)
                
                if re.match(r'^\*\*(.*)\*\*$', stripped_line):
                    content = stripped_line.replace('**', '').strip()
                    html_lines.append(f"<b><font color='{accent_color_hex}'>{content}</font></b>")
                elif stripped_line.startswith('* '):
                    content_final = process_inline_markdown(content_spoilers_processed[2:])
                    html_lines.append(f"&nbsp;&nbsp;•&nbsp;&nbsp;<b>{content_final}</b>")
                elif stripped_line.startswith('- '):
                    content_final = process_inline_markdown(content_spoilers_processed[2:])
                    html_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;{content_final}")
                else:
                    html_lines.append(process_inline_markdown(content_spoilers_processed))

            html_text = '<br>'.join(html_lines)
            html_text = re.sub(r'(<br>\s*){2,}', '<br><br>', html_text)
            
            if hasattr(Html, 'FROM_HTML_MODE_LEGACY'):
                faq_text_view.setText(Html.fromHtml(html_text, Html.FROM_HTML_MODE_LEGACY))
            else:
                faq_text_view.setText(Html.fromHtml(html_text))
            
            faq_text_view.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            faq_text_view.setMovementMethod(LinkMovementMethod.getInstance())
            faq_text_view.setLinkTextColor(Theme.getColor(Theme.key_dialogTextLink))
            faq_text_view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15)
            faq_text_view.setLineSpacing(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 2.0, activity.getResources().getDisplayMetrics()), 1.2)
            
            layout.addView(faq_text_view)
            scroller.addView(layout)
            builder.set_view(scroller)
            builder.set_positive_button("Close", None)
            builder.show()
        except Exception:
            log(f"[{self.id}] ERROR showing FAQ dialog: {traceback.format_exc()}")

    def _load_forwarding_rules(self):
        """Loads forwarding rules from persistent storage."""
        try:
            rules_str = self.get_setting(FORWARDING_RULES_KEY, "{}")
            self.forwarding_rules = {int(k): v for k, v in json.loads(rules_str).items()}
        except Exception:
            self.forwarding_rules = {}

    def _save_forwarding_rules(self):
        """Saves the current forwarding rules to persistent storage."""
        self.set_setting(FORWARDING_RULES_KEY, json.dumps({str(k): v for k, v in self.forwarding_rules.items()}))
        self._load_forwarding_rules()

    def _copy_to_clipboard(self, text_to_copy: str, label: str):
        """Copies text to the clipboard and shows a toast notification."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
            clip = ClipData.newPlainText(label, text_to_copy)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(activity, f"{label} address copied to clipboard!", Toast.LENGTH_SHORT).show()
        except Exception:
            log(f"[{self.id}] Failed to copy to clipboard: {traceback.format_exc()}")

    def _get_id_from_peer(self, peer):
        """Extracts a standard numerical ID from a TLRPC Peer object."""
        if not peer: return 0
        if isinstance(peer, TLRPC.TL_peerChannel): return -peer.channel_id
        if isinstance(peer, TLRPC.TL_peerChat): return -peer.chat_id
        if isinstance(peer, TLRPC.TL_peerUser): return peer.user_id
        return 0

    def _get_id_for_storage(self, entity):
        """Gets the correct ID for storing in rules (negative for chats/channels)."""
        if not entity: return 0
        return -entity.id if not isinstance(entity, TLRPC.TL_user) else entity.id

    def _get_chat_entity_from_input_id(self, input_id: int):
        """Retrieves a user or chat object from a numerical ID by checking local cache."""
        if input_id == 0: return None
        abs_id = abs(input_id)
        controller = get_messages_controller()
        entity = controller.getChat(abs_id)
        if entity: return entity
        if input_id > 0: return controller.getUser(input_id)
        return None

    def _sanitize_chat_id_for_request(self, input_id: int) -> int:
        """Converts a user-provided ID into a server-compatible short ID for channel/supergroup lookups."""
        id_str = str(abs(input_id))
        if id_str.startswith("100") and len(id_str) > 9:
            try:
                return int(id_str[3:])
            except (ValueError, IndexError):
                pass
        return abs(input_id)

    def _get_chat_entity(self, dialog_id):
        """A robust way to get a chat entity from a dialog_id."""
        if not isinstance(dialog_id, int):
            try: dialog_id = int(dialog_id)
            except (ValueError, TypeError): return None
        return get_messages_controller().getUser(dialog_id) if dialog_id > 0 else get_messages_controller().getChat(abs(dialog_id))

    def _get_entity_name(self, entity):
        """Gets a display-friendly name for a user, chat, or channel entity."""
        if not entity: return "Unknown"
        if hasattr(entity, 'title'): return entity.title
        if hasattr(entity, 'first_name'):
            name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
            return name if name else f"ID: {entity.id}"
        return f"ID: {getattr(entity, 'id', 'N/A')}"

    def _get_entity_tag(self, entity):
        """Gets an @username tag or falls back to the entity name."""
        if not entity: return "Unknown"
        if hasattr(entity, 'username') and entity.username:
            return f"@{entity.username}"
        return self._get_entity_name(entity)

    def _get_chat_name(self, chat_id):
        """A convenience function to get a chat name directly from its ID."""
        return self._get_entity_name(self._get_chat_entity(int(chat_id)))

    def _get_original_author_details(self, fwd_header):
        """Helper to extract original author details from a fwd_header."""
        if not fwd_header: return None, None
        original_author_name = None
        original_author_entity = None
        original_author_id = self._get_id_from_peer(getattr(fwd_header, 'from_id', None))
        if original_author_id:
            original_author_entity = self._get_chat_entity(original_author_id)
        if original_author_entity:
            original_author_name = self._get_entity_name(original_author_entity)
        elif hasattr(fwd_header, 'from_name') and fwd_header.from_name:
            original_author_name = fwd_header.from_name
        return original_author_name, original_author_entity

    def _prepare_final_entities(self, prefix_text, prefix_entities, original_entities):
        """Combines prefix entities (headers/quotes) and original message entities, adjusting offsets."""
        final_entities = ArrayList()
        if prefix_entities:
            final_entities.addAll(prefix_entities)
        
        if original_entities and not original_entities.isEmpty():
            offset_shift = self._get_java_len(prefix_text) + 2 if prefix_text else 0
            for i in range(original_entities.size()):
                old = original_entities.get(i)
                new = type(old)();
                new.offset, new.length = old.offset + offset_shift, old.length
                if hasattr(old, 'url'): new.url = old.url
                if hasattr(old, 'user_id'): new.user_id = old.user_id
                final_entities.add(new)
        return final_entities

    def _build_forward_header(self, message, source_entity, author_entity):
        """Constructs the 'Forwarded from...' text and its interactive entities."""
        is_channel = isinstance(source_entity, TLRPC.TL_channel) and not getattr(source_entity, 'megagroup', False)
        is_group = isinstance(source_entity, TLRPC.TL_chat) or (isinstance(source_entity, TLRPC.TL_channel) and getattr(source_entity, 'megagroup', True))
        
        if is_channel:
            return self._build_channel_header(message, source_entity)
        if is_group:
            return self._build_group_header(message, source_entity, author_entity)
        
        me = get_user_config().getCurrentUser()
        sender, receiver = (author_entity, source_entity) if message.out else (author_entity, me)
        return self._build_private_header(message, sender, receiver)

    def _build_channel_header(self, message, channel):
        """Builds the header for forwards from a channel, creating a clickable link."""
        name = self._get_entity_name(channel)
        entities = ArrayList()
        original_author_name, _ = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {name}"
        if original_author_name:
            text += f" (fwd_from {original_author_name})"
        
        link = TLRPC.TL_messageEntityTextUrl();
        link.offset, link.length = text.find(name), self._get_java_len(name)
        msg_id = message.fwd_from.channel_post if message.fwd_from and message.fwd_from.channel_post else message.id
        link.url = f"https://t.me/{channel.username}/{msg_id}" if channel.username else f"https://t.me/c/{channel.id}/{msg_id}"
        entities.add(link)
        return text, entities

    def _build_group_header(self, message, group, author):
        """Builds the header for forwards from a group, with mentions and links."""
        group_name = self._get_entity_name(group)
        author_name = self._get_entity_name(author)
        entities = ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {group_name} (by {author_name})"
        if original_author_name:
            text += f" fwd_from {original_author_name}"

        if isinstance(group, TLRPC.TL_channel):
            msg_id = message.id
            group_link = f"https://t.me/{group.username}/{msg_id}" if group.username else f"https://t.me/c/{group.id}/{msg_id}"
            link_entity = TLRPC.TL_messageEntityTextUrl();
            link_entity.offset, link_entity.length, link_entity.url = text.find(group_name), self._get_java_len(group_name), group_link
            entities.add(link_entity)
        else:
            bold = TLRPC.TL_messageEntityBold();
            bold.offset, bold.length = text.find(group_name), self._get_java_len(group_name)
            entities.add(bold)

        if author and isinstance(author, TLRPC.TL_user):
            self._add_user_entities(entities, text, author, author_name)
        
        if original_author_entity and isinstance(original_author_entity, TLRPC.TL_user):
            self._add_user_entities(entities, text, original_author_entity, original_author_name)
            
        return text, entities

    def _build_private_header(self, message, sender, receiver):
        """Builds the header for private chats, mentioning users where possible."""
        sender_name = self._get_entity_name(sender)
        receiver_name = self._get_entity_name(receiver)
        entities = ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {sender_name} to {receiver_name}"
        if original_author_name:
            text += f" (original fwd_from {original_author_name})"

        for entity, name in [(sender, sender_name), (receiver, receiver_name), (original_author_entity, original_author_name)]:
            if entity and isinstance(entity, TLRPC.TL_user):
                self._add_user_entities(entities, text, entity, name)
                
        return text, entities

    def _add_chat_menu_item(self):
        """Adds the 'Auto Forward' item to the chat menu."""
        self.add_menu_item(MenuItemData(
            menu_type=MenuItemType.CHAT_ACTION_MENU,
            text="Auto Forward...",
            icon="msg_forward",
            on_click=self._on_menu_item_click
        ))

    def _on_menu_item_click(self, context):
        """Handles the click event for the chat menu item."""
        current_chat_id = context.get("dialog_id")
        if not current_chat_id: return
        current_chat_id = int(current_chat_id)
        
        if current_chat_id in self.forwarding_rules:
            run_on_ui_thread(lambda: self._show_rule_action_dialog(current_chat_id))
        else:
            source_name = self._get_chat_name(current_chat_id)
            run_on_ui_thread(lambda: self._show_destination_input_dialog(current_chat_id, source_name))

    def _show_rule_action_dialog(self, source_id):
        """Shows a dialog to either modify or delete a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Manage Rule")
        builder.set_message(f"What would you like to do with the rule for '{self._get_chat_name(source_id)}'?")
        builder.set_positive_button("Modify", lambda b, w: self._launch_modification_dialog(source_id))
        builder.set_neutral_button("Cancel", lambda b, w: b.dismiss())
        builder.set_negative_button("Delete", lambda b, w: self._delete_rule_with_confirmation(source_id))
        run_on_ui_thread(lambda: builder.show())

    def _launch_modification_dialog(self, source_id):
        """Fetches existing rule data and launches the setup dialog to modify it."""
        rule_data = self.forwarding_rules.get(source_id)
        if not rule_data:
            BulletinHelper.show_error("Could not find rule to modify.")
            return
        source_name = self._get_chat_name(source_id)
        run_on_ui_thread(lambda: self._show_destination_input_dialog(source_id, source_name, existing_rule=rule_data))

    def _show_destination_input_dialog(self, source_id, source_name, existing_rule=None):
        """Displays the main dialog to set up or modify a forwarding rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            title = f"Modify Rule for '{source_name}'" if existing_rule else f"Set Destination for '{source_name}'"
            builder.set_title(title)
            
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))
            
            main_layout = LinearLayout(activity)
            main_layout.setOrientation(LinearLayout.VERTICAL)
            main_layout.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 4)
            
            input_field = EditText(activity)
            input_field_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            input_field_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            input_field.setHint("Destination Link, @username, or ID")
            input_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            input_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            input_field.setLayoutParams(input_field_params)
            main_layout.addView(input_field)

            keyword_filter_input = EditText(activity)
            keyword_filter_input_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            keyword_filter_input_params.setMargins(margin_px, margin_px // 4, margin_px, margin_px // 2)
            keyword_filter_input.setHint("Keyword/Regex Filter (optional)")
            keyword_filter_input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            keyword_filter_input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            keyword_filter_input.setLayoutParams(keyword_filter_input_params)
            main_layout.addView(keyword_filter_input)
            
            checkbox_tint_list = ColorStateList([[-16842912], [16842912]], [Theme.getColor(Theme.key_checkbox), Theme.getColor(Theme.key_checkboxCheck)])
            
            checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            checkbox_params.setMargins(margin_px, 0, margin_px, 0)
    
            drop_author_checkbox = CheckBox(activity)
            drop_author_checkbox.setText("Remove Original Author (Copy)")
            drop_author_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            drop_author_checkbox.setButtonTintList(checkbox_tint_list)
            drop_author_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(drop_author_checkbox)
    
            quote_replies_checkbox = CheckBox(activity)
            quote_replies_checkbox.setText("Quote Replies")
            quote_replies_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            quote_replies_checkbox.setButtonTintList(checkbox_tint_list)
            quote_replies_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(quote_replies_checkbox)
            
            divider_height_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 1, activity.getResources().getDisplayMetrics()))
            divider_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, divider_height_px)
            extra_left_margin_dp = 16 
            extra_left_margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, extra_left_margin_dp, activity.getResources().getDisplayMetrics()))
            
            vertical_margin_dp = 12
            vertical_margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, vertical_margin_dp, activity.getResources().getDisplayMetrics()))
            divider_params.setMargins(margin_px + extra_left_margin_px, vertical_margin_px, margin_px, vertical_margin_px)
    
            divider_one = View(activity)
            divider_one.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_one.setLayoutParams(divider_params)
            main_layout.addView(divider_one)
    
            # --- Author Type Checkboxes ---
            author_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            author_header_params.setMargins(margin_px, 0, margin_px, 0)
            author_header = TextView(activity)
            author_header.setText("Forward messages from:")
            author_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            author_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            author_header.setLayoutParams(author_header_params)
            main_layout.addView(author_header)
    
            forward_users_checkbox = CheckBox(activity)
            forward_users_checkbox.setText("Users")
            forward_users_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_users_checkbox.setButtonTintList(checkbox_tint_list)
            forward_users_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_users_checkbox)
            
            forward_bots_checkbox = CheckBox(activity)
            forward_bots_checkbox.setText("Bots")
            forward_bots_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_bots_checkbox.setButtonTintList(checkbox_tint_list)
            forward_bots_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_bots_checkbox)
    
            forward_outgoing_checkbox = CheckBox(activity)
            forward_outgoing_checkbox.setText("Outgoing Messages")
            forward_outgoing_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_outgoing_checkbox.setButtonTintList(checkbox_tint_list)
            forward_outgoing_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_outgoing_checkbox)
            
            divider_two = View(activity)
            divider_two.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_two.setLayoutParams(divider_params)
            main_layout.addView(divider_two)
            
            # --- Content Filter Section ---
            filter_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            filter_header_params.setMargins(margin_px, 0, margin_px, 0)
            filter_header = TextView(activity)
            filter_header.setText("Content to forward:")
            filter_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            filter_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            filter_header.setLayoutParams(filter_header_params)
            main_layout.addView(filter_header)
            
            filter_checkboxes = {}
            for key, label in FILTER_TYPES.items():
                cb = CheckBox(activity)
                cb.setText(label)
                cb.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                cb.setButtonTintList(checkbox_tint_list)
                cb.setLayoutParams(checkbox_params)
                main_layout.addView(cb)
                filter_checkboxes[key] = cb
    
            if existing_rule:
                destination_id = existing_rule.get("destination", 0)
                dest_entity = self._get_chat_entity(destination_id)
                identifier_to_set = str(destination_id)
                if dest_entity and hasattr(dest_entity, 'username') and dest_entity.username:
                    identifier_to_set = f"@{dest_entity.username}"
                input_field.setText(identifier_to_set)
                
                keyword_filter_input.setText(existing_rule.get("keyword_pattern", ""))
                drop_author_checkbox.setChecked(existing_rule.get("drop_author", False))
                quote_replies_checkbox.setChecked(existing_rule.get("quote_replies", True))
                
                forward_users_checkbox.setChecked(existing_rule.get("forward_users", True))
                forward_bots_checkbox.setChecked(existing_rule.get("forward_bots", True))
                forward_outgoing_checkbox.setChecked(existing_rule.get("forward_outgoing", True))
                
                current_filters = existing_rule.get("filters", {})
                for key, cb in filter_checkboxes.items():
                    cb.setChecked(current_filters.get(key, True))
            else:
                drop_author_checkbox.setChecked(False)
                quote_replies_checkbox.setChecked(True)
                forward_users_checkbox.setChecked(True)
                forward_bots_checkbox.setChecked(True)
                forward_outgoing_checkbox.setChecked(True)
                for cb in filter_checkboxes.values():
                    cb.setChecked(True)
    
            scroller = ScrollView(activity)
            scroller.addView(main_layout)
            builder.set_view(scroller)
            
            def on_set_click(b, w):
                filter_settings = {key: cb.isChecked() for key, cb in filter_checkboxes.items()}
                self._process_destination_input(
                    source_id,
                    source_name,
                    input_field.getText().toString(),
                    keyword_filter_input.getText().toString(),
                    drop_author_checkbox.isChecked(),
                    quote_replies_checkbox.isChecked(),
                    forward_users_checkbox.isChecked(),
                    forward_bots_checkbox.isChecked(),
                    forward_outgoing_checkbox.isChecked(),
                    filter_settings
                )
            
            builder.set_positive_button("Set", on_set_click)
            builder.set_negative_button("Cancel", lambda b, w: b.dismiss())
            run_on_ui_thread(lambda: builder.show())
        except Exception:
            log(f"[{self.id}] ERROR showing rule setup dialog: {traceback.format_exc()}")

    def _process_destination_input(self, source_id, source_name, user_input, keyword_pattern, drop_author, quote_replies, forward_users, forward_bots, forward_outgoing, filter_settings):
        """Handles all destination types with a multi-step resolution logic."""
        cleaned_input = (user_input or "").strip()
        if not cleaned_input: return

        # A dictionary to pass all the rule settings neatly.
        rule_settings = {
            "keyword_pattern": keyword_pattern,
            "drop_author": drop_author,
            "quote_replies": quote_replies,
            "forward_users": forward_users,
            "forward_bots": forward_bots,
            "forward_outgoing": forward_outgoing,
            "filter_settings": filter_settings
        }

        if "/joinchat/" in cleaned_input or "/+" in cleaned_input:
            self._resolve_as_invite_link(cleaned_input, source_id, source_name, rule_settings)
            return
        
        try:
            input_as_int = int(cleaned_input)
            cached_entity = self._get_chat_entity_from_input_id(input_as_int)
            if cached_entity:
                self._finalize_rule(source_id, source_name, self._get_id_for_storage(cached_entity), self._get_entity_name(cached_entity), rule_settings)
                return
            self._resolve_by_id_shotgun(input_as_int, source_id, source_name, rule_settings)
        except ValueError:
            self._resolve_as_username(cleaned_input, source_id, source_name, rule_settings)

    def _resolve_as_invite_link(self, cleaned_input, source_id, source_name, rule_settings):
        """Resolves a destination using a t.me/joinchat/... link."""
        try:
            hash_val = cleaned_input.split("/")[-1]
            req = TLRPC.TL_messages_checkChatInvite(); req.hash = hash_val
            
            def on_check_invite(response, error):
                if error or not response or not hasattr(response, 'chat'):
                    error_text = getattr(error, 'text', 'Invalid or expired link')
                    BulletinHelper.show_error(f"Failed to resolve link: {error_text}")
                    return
                dest_entity = response.chat
                if dest_entity:
                    get_messages_controller().putChat(dest_entity, False)
                    dest_id = self._get_id_for_storage(dest_entity)
                    self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            
            send_request(req, RequestCallback(on_check_invite))
        except Exception as e:
            log(f"[{self.id}] Failed to process invite link: {e}")

    def _resolve_by_id_shotgun(self, input_as_int, source_id, source_name, rule_settings):
        """Resolves a numeric ID that is not in the local cache by making a network request."""
        log(f"[{self.id}] ID {input_as_int} not in cache. Attempting network lookup.")
        
        def on_get_chats_complete(response, error):
            if error or not response or not hasattr(response, 'chats') or response.chats.isEmpty():
                error_text = getattr(error, 'text', 'Not found')
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}. Reason: {error_text}")
                return
            
            dest_entity = response.chats.get(0)
            if dest_entity:
                get_messages_controller().putChat(dest_entity, True)
                dest_id = self._get_id_for_storage(dest_entity)
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            else:
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}")

        req = TLRPC.TL_messages_getChats()
        id_list = ArrayList()
        possible_ids = HashSet()
        sanitized_short_id = self._sanitize_chat_id_for_request(input_as_int)
        possible_ids.add(sanitized_short_id)
        possible_ids.add(-sanitized_short_id)
        possible_ids.add(abs(input_as_int))
        possible_ids.add(-abs(input_as_int))
        id_list.addAll(possible_ids)
        req.id = id_list
        send_request(req, RequestCallback(on_get_chats_complete))

    def _resolve_as_username(self, username, source_id, source_name, rule_settings):
        """Resolver for public links and @usernames."""
        log(f"[{self.id}] Resolving '{username}' as a username/public link.")
        
        def on_resolve_complete(response, error):
            if error or not response:
                error_text = getattr(error, 'text', 'Not found')
                BulletinHelper.show_error(f"Could not resolve '{username}': {error_text}")
                return
            
            dest_entity = None
            if hasattr(response, 'chats') and response.chats and not response.chats.isEmpty():
                dest_entity = response.chats.get(0)
                get_messages_controller().putChats(response.chats, False)
            elif hasattr(response, 'users') and response.users and not response.users.isEmpty():
                dest_entity = response.users.get(0)
                get_messages_controller().putUsers(response.users, False)
            
            if dest_entity:
                dest_id = self._get_id_for_storage(dest_entity)
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            else:
                BulletinHelper.show_error(f"Could not resolve '{username}'.")
        
        try:
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = username.replace("@", "").split("/")[-1]
            send_request(req, RequestCallback(on_resolve_complete))
        except Exception:
            log(f"[{self.id}] ERROR resolving username: {traceback.format_exc()}")

    def _finalize_rule(self, source_id, source_name, destination_id, dest_name, rule_settings):
        """Saves a fully resolved rule to storage and shows a success message."""
        if destination_id == 0:
            log(f"[{self.id}] Finalize rule called with invalid destination_id=0. Aborting.")
            BulletinHelper.show_error("Failed to save rule: Invalid destination chat resolved.")
            return
            
        rule_data = {
            "destination": destination_id,
            "enabled": True,
            "keyword_pattern": rule_settings["keyword_pattern"],
            "drop_author": rule_settings["drop_author"],
            "quote_replies": rule_settings["quote_replies"],
            "forward_users": rule_settings["forward_users"],
            "forward_bots": rule_settings["forward_bots"],
            "forward_outgoing": rule_settings["forward_outgoing"],
            "filters": rule_settings["filter_settings"]
        }
        self.forwarding_rules[source_id] = rule_data
        self._save_forwarding_rules()
        run_on_ui_thread(lambda: self._show_success_dialog(source_name, dest_name))

    def _show_success_dialog(self, source_name, dest_name):
        """Shows a success message after a rule is set."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Success!");
        builder.set_message(f"Rule for '{source_name}' set to '{dest_name}'.")
        builder.set_positive_button("OK", lambda b, w: b.dismiss())
        run_on_ui_thread(lambda: builder.show())

    def _delete_rule_with_confirmation(self, source_id):
        """Shows a confirmation dialog before deleting a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Delete Rule?")
            builder.set_message(f"Are you sure you want to delete the rule for '{self._get_chat_name(source_id)}'?")
            builder.set_positive_button("Delete", lambda b, w: self._execute_delete(source_id));
            builder.set_negative_button("Cancel", None)
            builder.show()
        except Exception:
            log(f"[{self.id}] ERROR in delete confirmation: {traceback.format_exc()}")

    def _execute_delete(self, source_id):
        """Deletes a rule and refreshes the settings UI."""
        if source_id in self.forwarding_rules:
            del self.forwarding_rules[source_id]
            self._save_forwarding_rules()
            run_on_ui_thread(lambda: self._refresh_settings_ui())

    def _refresh_settings_ui(self):
        """Forces the settings page to rebuild its views to show changes."""
        try:
            last_fragment = get_last_fragment()
            if isinstance(last_fragment, PluginSettingsActivity) and hasattr(last_fragment, 'rebuildViews'):
                last_fragment.rebuildViews()
        except Exception:
            log(f"[{self.id}] ERROR during UI refresh: {traceback.format_exc()}")
    
    # --- Auto-Updater Methods ---

    def _updater_loop(self):
        """The main loop for the background updater thread."""
        log(f"[{self.id}] Updater loop started.")
        time.sleep(60) 
        
        while not self.stop_updater_thread.is_set():
            self.check_for_updates(is_manual=False)
            self.stop_updater_thread.wait(self.UPDATE_INTERVAL_SECONDS)
        log(f"[{self.id}] Updater loop finished.")

    def check_for_updates(self, is_manual=False):
        """Public method to trigger an update check."""
        if is_manual:
            run_on_ui_thread(lambda: BulletinHelper.show_info("Checking for updates..."))
        threading.Thread(target=self._perform_update_check, args=[is_manual]).start()

    def _perform_update_check(self, is_manual):
        """Connects to GitHub API and checks for a new version."""
        try:
            api_url = URL(f"https://api.github.com/repos/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/releases/latest")
            connection = api_url.openConnection()
            connection.setRequestMethod("GET")
            connection.connect()

            if connection.getResponseCode() == HttpURLConnection.HTTP_OK:
                stream = connection.getInputStream()
                scanner = Scanner(stream, "UTF-8").useDelimiter("\\A")
                response_str = scanner.next() if scanner.hasNext() else ""
                scanner.close()
                
                release_data = json.loads(response_str)
                latest_version_tag = release_data.get("tag_name", "0.0.0").lstrip('v')
                current_version = __version__

                latest_v_tuple = tuple(map(int, latest_version_tag.split('.')))
                current_v_tuple = tuple(map(int, current_version.split('.')))

                if latest_v_tuple > current_v_tuple:
                    changelog = release_data.get("body", "No changelog provided.")
                    assets = release_data.get("assets", [])
                    download_url = None
                    for asset in assets:
                        if asset.get("name", "").endswith(".py"):
                            download_url = asset.get("browser_download_url")
                            break
                    
                    if download_url:
                        run_on_ui_thread(lambda: self._show_update_dialog(latest_version_tag, changelog, download_url))
                    elif is_manual:
                        run_on_ui_thread(lambda: BulletinHelper.show_error("Update found, but no download file available."))
                elif is_manual:
                    run_on_ui_thread(lambda: BulletinHelper.show_info("You are on the latest version!", 2000))
            elif is_manual:
                run_on_ui_thread(lambda: BulletinHelper.show_error(f"Failed to fetch updates (HTTP {connection.getResponseCode()})"))

        except Exception as e:
            log(f"[{self.id}] Update check failed: {traceback.format_exc()}")
            if is_manual:
                run_on_ui_thread(lambda: BulletinHelper.show_error("Update check failed. See logs."))

    def _show_update_dialog(self, version, changelog, download_url):
        """Displays a dialog with the changelog and update/cancel buttons."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return

        builder = AlertDialogBuilder(activity)
        builder.set_title(f"Update to v{version} available!")

        margin_dp = 20
        margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))
        scroller = ScrollView(activity)
        changelog_view = TextView(activity)
        changelog_view.setPadding(margin_px, 0, margin_px, margin_px // 2)

        html_text = self._process_changelog_markdown(changelog)
        if hasattr(Html, 'FROM_HTML_MODE_LEGACY'):
            changelog_view.setText(Html.fromHtml(html_text, Html.FROM_HTML_MODE_LEGACY))
        else:
            changelog_view.setText(Html.fromHtml(html_text))
        
        changelog_view.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
        changelog_view.setLinkTextColor(Theme.getColor(Theme.key_dialogTextLink))
        changelog_view.setMovementMethod(LinkMovementMethod.getInstance())
        changelog_view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15)
        scroller.addView(changelog_view)
        builder.set_view(scroller)

        on_update_click = lambda b, w: threading.Thread(target=self._download_and_install, args=[download_url, version]).start()
        builder.set_positive_button("Update", on_update_click)
        builder.set_negative_button("Cancel", None)
        builder.show()

    def _download_and_install(self, url, version):
        """Downloads and installs the update seamlessly."""
        try:
            run_on_ui_thread(lambda: BulletinHelper.show_info(f"Downloading update v{version}..."))

            download_url = URL(url)
            connection = download_url.openConnection()
            connection.connect()

            if connection.getResponseCode() == HttpURLConnection.HTTP_OK:
                plugins_controller = PluginsController.getInstance()
                cache_dir = File(plugins_controller.pluginsDir, ".cache")
                cache_dir.mkdirs()
                
                temp_file = File(cache_dir, f"temp_{self.id}_v{version}.py")

                input_stream = connection.getInputStream()
                output_stream = FileOutputStream(temp_file)
                buffer = bytearray(4096)
                bytes_read = input_stream.read(buffer)
                while bytes_read != -1:
                    output_stream.write(buffer, 0, bytes_read)
                    bytes_read = input_stream.read(buffer)
                output_stream.close()
                input_stream.close()

                log(f"[{self.id}] Download complete. Installing from {temp_file.getAbsolutePath()}")

                def on_install_callback(error_msg):
                    if error_msg:
                        log(f"[{self.id}] Installation failed: {error_msg}")
                        run_on_ui_thread(lambda: BulletinHelper.show_error(f"Update failed: {error_msg}"))
                    else:
                        log(f"[{self.id}] Update to v{version} successful! Closing settings page.")
                        
                        def close_settings_action():
                            """Safely closes the current settings fragment."""
                            fragment = get_last_fragment()
                            if fragment and hasattr(fragment, 'finishFragment'):
                                fragment.finishFragment()
                
                        # Button "DONE", the action to close the settings page.
                        run_on_ui_thread(lambda: BulletinHelper.show_with_button(
                            f"Update v{version} installed!",
                            R.raw.chats_infotip,
                            "DONE",
                            lambda: close_settings_action()
                        ))
                    if temp_file.exists():
                        temp_file.delete()
                
                install_callback_proxy = self.InstallCallback(on_install_callback)
                plugins_controller.loadPluginFromFile(temp_file.getAbsolutePath(), install_callback_proxy)

            else:
                 run_on_ui_thread(lambda: BulletinHelper.show_error("Download failed."))
        except Exception:
            log(f"[{self.id}] Download and install failed: {traceback.format_exc()}")
            run_on_ui_thread(lambda: BulletinHelper.show_error("An error occurred during update."))


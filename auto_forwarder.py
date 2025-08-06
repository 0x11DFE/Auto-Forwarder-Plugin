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
from android.widget import EditText, FrameLayout, CheckBox, LinearLayout, TextView, Toast, ScrollView, CompoundButton
from android.text import InputType, Html
from android.text.method import LinkMovementMethod
from android.util import TypedValue
from android.view import View, ViewGroup
from java.util import ArrayList, HashSet, Scanner
from android.content.res import ColorStateList
from android.content import ClipData, ClipboardManager, Context
from android.os import Handler, Looper
from java.lang import Runnable, String as JavaString, Integer
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
__version__ = "1.8.0"
__min_version__ = "11.9.1"
__icon__ = "Putin_1337/14"

# --- Configuration Constants ---
FORWARDING_RULES_KEY = "forwarding_rules_v1337"
DEFAULT_SETTINGS = {
    "deferral_timeout_ms": 5000,
    "min_msg_length": 1,
    "max_msg_length": 4096,
    "deduplication_window_seconds": 10.0,
    "album_timeout_ms": 800,
    "antispam_delay_seconds": 1.0
}
FILTER_TYPES = collections.OrderedDict([
    ("text", "Text Messages"),
    ("media_captions", "Media Captions"),
    ("photos", "Photos"),
    ("videos", "Videos"),
    ("documents", "Files / Documents"),
    ("audio", "Audio Files"),
    ("voice", "Voice Messages"),
    ("video_messages", "Video Messages (Roundies)"),
    ("stickers", "Stickers"),
    ("gifs", "GIFs & Animations")
])
FAQ_TEXT = """--- **Disclaimer and Responsible Usage** ---
Please be aware that using a plugin like this automates actions on your personal Telegram account. This practice is often referred to as 'self-botting'.
This kind of automation may be considered a violation of [Telegram's Terms of Service](https://telegram.org/tos), which can prohibit bot-like activity from user accounts.
Using this plugin carries potential risks, including account limitations or bans. You accept full responsibility for your actions. The author is not responsible for any consequences from your use or misuse of this tool.
**Use at your own risk.**

--- **FAQ** ---
**🚀 Core Functionality**
* **How do I create a rule?**
Go into any chat you want to forward messages *from*. Tap the three-dots menu (⋮) in the top right and select "Auto Forward...". A dialog will then ask for the destination chat.
* **How do I set the destination automatically?**
In the rule setup dialog, tap "Set by Replying". Then, go to the destination chat (or a comment thread/topic within it), and reply to *any* message (or not) with the exact word `set`. The plugin will detect this, set the destination, and auto-delete your message.
* **How do I edit or delete a rule?**
Go to a chat where a rule is active and open the "Auto Forward..." menu item again. A "Manage Rule" dialog will appear, allowing you to modify or delete it. You can also manage all rules from the main plugin settings page.
* **What's the difference between "Copy" and "Forward" mode?**
When setting up a rule, you have a checkbox for "Remove Original Author".
- **Checked (Copy Mode):** Sends a brand new message to the destination. It looks like you sent it yourself. All text formatting is preserved.
- **Unchecked (Forward Mode):** This option is not implemented in Copy mode. The plugin primarily operates by copying messages.
* **Can I control which messages get forwarded?**
Yes. When creating or modifying a rule, you can choose to forward messages from regular users, bots, and your own outgoing messages independently. You can also filter incoming messages to only forward from specific users or bots.

--- **✨ Advanced Features & Formatting** ---
* **How does forwarding to a topic work?**
Use the "Set by Replying" feature. Go into the specific comment thread (topic) you want to forward to and reply to any message there with `set`. The plugin will automatically save the correct ID for that thread.
* **How does the Anti-Spam Firewall work?**
It's a rate-limiter that prevents a single user from flooding your destination chat. It works by enforcing a minimum time delay between forwards *from the same person*. You can configure this delay in the General Settings.
* **How do the content filters work?**
When creating or modifying a rule, you'll see checkboxes for different message types (Text, Photos, Videos, etc.). Simply uncheck any content type you *don't* want to be forwarded for that specific rule. For example, you can set up a rule to forward only photos and videos from a channel, ignoring all text messages.
* **How does keyword/regex filtering work?**
You can specify keywords or regex patterns that messages must contain to be forwarded. This works for text messages, media captions, and **document filenames**:
- **Keywords:** Simple text matching (case-insensitive). Example: `"bitcoin"` will match messages containing "Bitcoin", "BITCOIN", etc.
- **Regex Patterns:** Advanced pattern matching. Example: `"\\\\b(btc|bitcoin|₿)\\\\b"` will match whole words containing btc, bitcoin, or the bitcoin symbol.
- **Leave the field empty** to disable keyword filtering (forward all messages that pass other filters).
- If a regex pattern fails to compile, it will fall back to simple case-insensitive text matching.
* **Does the plugin support text formatting (Markdown)?**
Yes, completely. The plugin perfectly preserves all text formatting from the original message. This includes:
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
- **Deduplication Window:** Prevents double-forwards. If Telegram sends a duplicate notification for the same message within this time window (in seconds), the plugin will ignore it. This window is also used for the new file name deduplication feature.
- **Anti-Spam Delay:** The core setting for the firewall, as explained above. Set to `0` to disable it.
* **Why do large files I send myself sometimes fail to forward?**
This is a known limitation. If your file takes longer to upload than the "Media Deferral Timeout", the plugin may not be able to forward it. The feature is most reliable for forwarding messages you receive or for your own small files that upload instantly.
"""

# --- Asynchronous Tasks & Proxies ---

class DeferredTask(dynamic_proxy(Runnable)):
    """A proxy class to run a message processing task after a delay."""
    def __init__(self, plugin, event_key):
        super().__init__()
        self.plugin = plugin
        self.event_key = event_key

    def run(self):
        self.plugin._process_timed_out_message(self.event_key)


class AlbumTask(dynamic_proxy(Runnable)):
    """A proxy class to run album processing after a short buffer period."""
    def __init__(self, plugin, grouped_id):
        super().__init__()
        self.plugin = plugin
        self.grouped_id = grouped_id

    def run(self):
        self.plugin._process_album(self.grouped_id)

# --- Main Plugin Class ---

class AutoForwarderPlugin(BasePlugin):
    """
    The main class for the Auto Forwarder plugin.
    This class handles settings, UI, rules, and the core forwarding logic.
    """
    # --- Constants ---
    TON_ADDRESS = "UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm"
    USDT_ADDRESS = "TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo"
    USER_TIMESTAMP_CACHE_SIZE = 500
    PROCESSED_FILES_CACHE_SIZE = 200
    GITHUB_OWNER = "0x11DFE"
    GITHUB_REPO = "Auto-Forwarder-Plugin"
    UPDATE_INTERVAL_SECONDS = 6 * 60 * 60

    # --- Nested Proxy Classes ---
    class InstallCallback(dynamic_proxy(Utilities.Callback)):
        """A proxy for handling the result of a plugin installation."""
        def __init__(self, callback_func):
            super().__init__()
            self.callback_func = callback_func
        
        def run(self, arg):
            try:
                self.callback_func(arg)
            except Exception:
                log(f"[{__id__}] Error in install callback proxy: {traceback.format_exc()}")

    class OnClickListenerProxy(dynamic_proxy(View.OnClickListener)):
        """A proxy class to handle Android's OnClickListener interface safely."""
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
    
        def onClick(self, view):
            try:
                self.callback(view)
            except Exception:
                log(f"[{__id__}] Error in OnClickListener proxy: {traceback.format_exc()}")
    
    # --- Initialization ---
    def __init__(self):
        """Initializes the plugin's state and properties."""
        super().__init__()
        self.id = __id__
        self.forwarding_rules = {}
        self.error_message = None
        self.deferred_messages = {}
        self.album_buffer = {}
        self.processed_keys = collections.deque(maxlen=200)
        self.handler = Handler(Looper.getMainLooper())
        self.user_last_message_time = collections.OrderedDict()
        self.processed_files_cache = collections.OrderedDict()
        self.updater_thread = None
        self.stop_updater_thread = threading.Event()
        
        # State for the "Set by Replying" feature
        self.is_listening_for_reply = False
        self.reply_listener_context = {}
        self.reply_listener_timeout_task = None
        
        # This holds our dedicated listener object to prevent lifecycle crashes.
        self.message_listener = None

        self._load_configurable_settings()

    # --- Dedicated Notification Listener ---
    class MessageListener(dynamic_proxy(NotificationCenter.NotificationCenterDelegate)):
        """
        A dedicated listener class to handle notifications from NotificationCenter.
        This isolates the listener from the main plugin object's lifecycle,
        preventing "PyObject is closed" errors during plugin reloads.
        """
        def __init__(self, plugin_instance):
            """Initializes the listener with a reference to the main plugin."""
            super().__init__()
            self.plugin = plugin_instance

        def didReceivedNotification(self, id, account, args):
            """The main entry point for all new message notifications."""
            if id != NotificationCenter.didReceiveNewMessages:
                return
            
            messages_list = args[1]
            
            # --- "SET BY REPLYING" LISTENER ---
            if self.plugin.is_listening_for_reply:
                for i in range(messages_list.size()):
                    msg_obj = messages_list.get(i)
                    msg = msg_obj.messageOwner
                    # Check for an outgoing reply with the trigger word 'set'.
                    if msg and msg.out and msg.message and msg.message.lower() == 'set':
                        # Defines a runnable task to process the trigger after a short delay.
                        class ProcessReplyRunnable(dynamic_proxy(Runnable)):
                            def __init__(self, plugin, message_object):
                                super().__init__()
                                self.plugin = plugin
                                self.message_object = message_object
                            def run(self):
                                self.plugin._process_reply_trigger(self.message_object)
                        
                        # We delay processing by 1.5 seconds. This is crucial to prevent a "race condition"
                        # where the plugin tries to delete the 'set' message before the server has
                        # confirmed it, which would cause the message to reappear.
                        self.plugin.handler.postDelayed(ProcessReplyRunnable(self.plugin, msg_obj), 1500)
            
            # --- REGULAR MESSAGE FORWARDING LOGIC ---
            try:
                if not self.plugin.forwarding_rules:
                    return
                for i in range(messages_list.size()):
                    message_object = messages_list.get(i)
                    if not (hasattr(message_object, 'messageOwner') and message_object.messageOwner):
                        continue
                    # Pass the event to the main handler in the plugin.
                    self.plugin.handle_message_event(message_object)
            except Exception:
                log(f"[{self.plugin.id}] ERROR in notification handler: {traceback.format_exc()}")

    # --- Plugin Lifecycle Methods ---
    def on_plugin_load(self):
        """Called when the plugin is loaded or reloaded."""
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
                # Create and register the dedicated listener object.
                self.message_listener = self.MessageListener(self)
                account_instance.getNotificationCenter().addObserver(self.message_listener, NotificationCenter.didReceiveNewMessages)
                log(f"[{self.id}] Message observer successfully registered.")

        run_on_ui_thread(register_observer)

    def on_plugin_unload(self):
        """Called when the plugin is unloaded."""
        self.stop_updater_thread.set()
        log(f"[{self.id}] Auto-updater thread stopped.")

        def unregister_observer():
            account_instance = get_account_instance()
            # Unregister the specific listener object if it exists to prevent memory leaks.
            if account_instance and self.message_listener:
                account_instance.getNotificationCenter().removeObserver(self.message_listener, NotificationCenter.didReceiveNewMessages)
                self.message_listener = None
                log(f"[{self.id}] Message observer successfully removed.")

        run_on_ui_thread(unregister_observer)
        self.handler.removeCallbacksAndMessages(None)

    # --- Settings and Configuration ---
    def _load_configurable_settings(self):
        """Loads user-configurable settings from storage into memory."""
        log(f"[{self.id}] Reloading configurable settings into memory.")
        self.min_msg_length = int(self.get_setting("min_msg_length", str(DEFAULT_SETTINGS["min_msg_length"])))
        self.max_msg_length = int(self.get_setting("max_msg_length", str(DEFAULT_SETTINGS["max_msg_length"])))
        self.deferral_timeout_ms = int(self.get_setting("deferral_timeout_ms", str(DEFAULT_SETTINGS["deferral_timeout_ms"])))
        self.album_timeout_ms = int(self.get_setting("album_timeout_ms", str(DEFAULT_SETTINGS["album_timeout_ms"])))
        self.deduplication_window_seconds = float(self.get_setting("deduplication_window_seconds", str(DEFAULT_SETTINGS["deduplication_window_seconds"])))
        self.antispam_delay_seconds = float(self.get_setting("antispam_delay_seconds", str(DEFAULT_SETTINGS["antispam_delay_seconds"])))

    def _load_forwarding_rules(self):
        """Loads all forwarding rules from JSON storage."""
        try:
            rules_str = self.get_setting(FORWARDING_RULES_KEY, "{}")
            self.forwarding_rules = {int(k): v for k, v in json.loads(rules_str).items()}
        except Exception: 
            self.forwarding_rules = {}

    def _save_forwarding_rules(self):
        """Saves all forwarding rules to JSON storage."""
        self.set_setting(FORWARDING_RULES_KEY, json.dumps({str(k): v for k, v in self.forwarding_rules.items()}))
        self._load_forwarding_rules() # Reload to ensure consistency

    # --- Core Logic & Event Handling ---
    def handle_message_event(self, message_object):
        """
        The main handler for processing a single incoming message object.
        It applies all filters and rules before deciding to forward.
        """
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule or not rule.get("enabled", False):
            return

        # 1. Filter by author type (user, bot, outgoing)
        author_type = self._get_author_type(message)
        if author_type == "outgoing" and not rule.get("forward_outgoing", True): return
        if author_type == "user" and not rule.get("forward_users", True): return
        if author_type == "bot" and not rule.get("forward_bots", True): return

        # 2. Filter by specific author usernames or IDs
        author_filter = rule.get("author_filter", "").strip()
        if author_filter and (author_type == "user" or author_type == "bot"):
            author_id = self._get_id_from_peer(message.from_id)
            author_entity = self._get_chat_entity(author_id)
            allowed_authors = [t.strip().lower().lstrip('@') for t in author_filter.split(',') if t.strip()]
            match_found = False
            if str(author_id) in allowed_authors:
                match_found = True
            if not match_found and author_entity and hasattr(author_entity, 'username') and author_entity.username:
                if author_entity.username.lower() in allowed_authors:
                    match_found = True
            if not match_found:
                log(f"[{self.id}] Dropping message from '{self._get_entity_name(author_entity)}' because it doesn't match author filter: '{author_filter}'")
                return

        # 3. Deduplicate based on filename to prevent spam
        if message_object.isDocument():
            doc = getattr(message.media, 'document', None)
            filename = self._get_document_filename(doc)
            if filename:
                author_id = get_user_config().getClientUserId() if message.out else self._get_id_from_peer(message.from_id)
                file_key = (author_id, filename)
                current_time = time.time()
                # Clean up old entries from the cache
                while self.processed_files_cache:
                    key, ts = next(iter(self.processed_files_cache.items()))
                    if current_time - ts > self.deduplication_window_seconds:
                        self.processed_files_cache.popitem(last=False)
                    else:
                        break
                if file_key in self.processed_files_cache:
                    log(f"[{self.id}] Deduplicating file '{filename}' from user {author_id} sent within the time window.")
                    return
                self.processed_files_cache[file_key] = current_time
                if len(self.processed_files_cache) > self.PROCESSED_FILES_CACHE_SIZE:
                    self.processed_files_cache.popitem(last=False)

        # 4. Handle albums by buffering them
        grouped_id = getattr(message, 'grouped_id', 0)
        if grouped_id != 0:
            if grouped_id not in self.album_buffer:
                log(f"[{self.id}] Detected start of new album: {grouped_id}")
                album_task = AlbumTask(self, grouped_id)
                self.album_buffer[grouped_id] = {'messages': [], 'task': album_task}
                self.handler.postDelayed(album_task, self.album_timeout_ms)
            self.album_buffer[grouped_id]['messages'].append(message_object)
            return

        # 5. Apply anti-spam delay
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

        # 6. Deduplicate based on message event key
        event_key = None
        if message.out:
            event_key = ("outgoing", message.dialog_id, message.date, message.message or "")
        else:
            author_id = self._get_id_from_peer(message.from_id)
            event_key = ("incoming", author_id, source_chat_id, message.id)
        if any(key == event_key for key, ts in self.processed_keys):
            return

        # 7. Defer forwarding if media is incomplete or reply object is missing
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

        # If this message was previously deferred, cancel the timeout task
        if event_key in self.deferred_messages:
            _, deferred_task = self.deferred_messages[event_key]
            self.handler.removeCallbacks(deferred_task)
            del self.deferred_messages[event_key]
        
        # 8. If all checks pass, proceed to sending
        self._process_and_send(message_object, rule)

    def _process_and_send(self, message_object, rule):
        """Performs final content checks and sends the message."""
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        
        # Create a unique key for deduplication
        if message.out:
            event_key = ("outgoing", message.dialog_id, message.date, message.message or "")
        else:
            author_id = self._get_id_from_peer(message.from_id)
            event_key = ("incoming", author_id, source_chat_id, message.id)

        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == event_key for key, ts in self.processed_keys):
            return

        # Filter by content type (text, photo, etc.)
        if not self._is_message_allowed_by_filters(message_object, rule):
            return

        # Filter by keywords/regex
        keyword_pattern = rule.get("keyword_pattern", "").strip()
        if keyword_pattern:
            text_to_check = message.message or ""
            if message_object.isDocument():
                doc = getattr(message.media, 'document', None)
                filename = self._get_document_filename(doc)
                if filename:
                    text_to_check = f"{text_to_check} {filename}".strip()
            if not self._passes_keyword_filter(text_to_check, keyword_pattern):
                return
        
        # Filter by message length
        is_text_based = not message.media or isinstance(message.media, (TLRPC.TL_messageMediaEmpty, TLRPC.TL_messageMediaWebPage))
        if is_text_based:
            if not (self.min_msg_length <= len(message.message or "") <= self.max_msg_length):
                return

        # Mark as processed and send
        self.processed_keys.append((event_key, time.time()))
        self._send_forwarded_message(message_object, rule)
    
    def _process_timed_out_message(self, event_key):
        """Processes a message that was deferred after the timeout has passed."""
        if event_key in self.deferred_messages:
            log(f"[{self.id}] Processing deferred message after timeout. Key: {event_key}")
            message_object, _ = self.deferred_messages[event_key]
            # The getMessage() method doesn't exist, so we removed the attempt
            # to re-fetch from cache and will proceed with the object we have.
            source_chat_id = self._get_id_from_peer(message_object.messageOwner.peer_id)
            rule = self.forwarding_rules.get(source_chat_id)
            if rule:
                self._process_and_send(message_object, rule)
            del self.deferred_messages[event_key]

    def _process_album(self, grouped_id):
        """Processes a collection of messages as a single album."""
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

        # Deduplicate the entire album
        album_key = (self._get_id_from_peer(first_message.from_id), source_chat_id, grouped_id)
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == album_key for key, ts in self.processed_keys):
            return
        self.processed_keys.append((album_key, time.time()))
        self._send_album(album_data['messages'], rule)

    # --- Message Sending and Formatting ---
    def _send_forwarded_message(self, message_object, rule):
        """Constructs and sends a single forwarded/copied message."""
        message = message_object.messageOwner
        if not message: return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        topic_id = rule.get("destination_topic_id", 0)
        
        try:
            input_media = self._get_input_media(message_object)
            has_media = bool(input_media)
            has_text = bool(message.message)

            original_text = ""
            if has_text:
                filters = rule.get("filters", {})
                if has_media and filters.get("media_captions", True):
                    original_text = message.message
                elif not has_media and filters.get("text", True):
                    original_text = message.message
            original_entities = message.entities if original_text else None

            # Build the prefix (forward header, quoted reply)
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
                            entity.offset += self._get_java_len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            # Combine prefix with the original message content
            message_text = f"{prefix_text}\n\n{original_text}".strip()
            entities = self._prepare_final_entities(prefix_text, prefix_entities, original_entities)

            # Build the appropriate request based on content
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
                # Add topic/reply info if applicable
                if topic_id > 0:
                    req.reply_to = TLRPC.TL_inputReplyToMessage()
                    req.reply_to.reply_to_msg_id = topic_id
                    req.flags |= 1 # Set the has_reply_to flag
                if entities and not entities.isEmpty():
                    req.entities = entities
                    req.flags |= 8 # Set the has_entities flag
                send_request(req, RequestCallback(lambda r, e: None))
        except Exception:
            log(f"[{self.id}] ERROR in _send_forwarded_message: {traceback.format_exc()}")
            
    def _send_album(self, message_objects, rule):
        """Constructs and sends a multi-media message (album)."""
        if not message_objects: return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})
        keyword_pattern = rule.get("keyword_pattern", "").strip()
        topic_id = rule.get("destination_topic_id", 0)

        try:
            # For albums, keyword check is performed on the combined captions and filenames
            if keyword_pattern:
                full_text_to_check = ""
                for msg_obj in message_objects:
                    msg = msg_obj.messageOwner
                    if not msg: continue
                    if msg.message: full_text_to_check += f" {msg.message}"
                    if msg_obj.isDocument():
                        doc = getattr(msg.media, 'document', None)
                        filename = self._get_document_filename(doc)
                        if filename: full_text_to_check += f" {filename}"
                if not self._passes_keyword_filter(full_text_to_check.strip(), keyword_pattern): return

            req = TLRPC.TL_messages_sendMultiMedia()
            req.peer = get_messages_controller().getInputPeer(to_peer_id)
            if topic_id > 0:
                req.reply_to = TLRPC.TL_inputReplyToMessage()
                req.reply_to.reply_to_msg_id = topic_id
                req.flags |= 1
                
            multi_media_list = ArrayList()
            # In an album, only the first item's caption is used.
            album_caption, album_entities = "", None
            if filters.get("media_captions", True):
                for msg_obj in message_objects:
                    if msg_obj.messageOwner and msg_obj.messageOwner.message:
                        album_caption, album_entities = msg_obj.messageOwner.message, msg_obj.messageOwner.entities
                        break

            first_message_obj, first_message = message_objects[0], message_objects[0].messageOwner
            
            # Build header/quote prefix, same as single messages
            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(first_message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(first_message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(first_message, source_entity, author_entity)
                    if header_text: prefix_text += header_text
                    if header_entities: prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(first_message_obj)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += self._get_java_len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            header_attached = False
            for original_msg_obj in message_objects:
                current_msg_obj = original_msg_obj
                # The getMessage() method doesn't exist, so the attempt to refresh
                # from cache has been removed.
                if not self._is_message_allowed_by_filters(current_msg_obj, rule): continue
                input_media = self._get_input_media(current_msg_obj)
                if not input_media: continue

                single_media = TLRPC.TL_inputSingleMedia()
                single_media.media = input_media
                single_media.random_id = random.getrandbits(63)

                # The prefix and album caption are attached only to the first item.
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
            
    def _build_reply_quote(self, message_object):
        """Builds a formatted blockquote string for a replied-to message."""
        replied_message_obj = message_object.replyMessageObject
        if not replied_message_obj or not replied_message_obj.messageOwner:
            return None, None
        
        replied_message = replied_message_obj.messageOwner
        author_id = self._get_id_from_peer(replied_message.from_id)
        author_entity = self._get_chat_entity(author_id)
        author_name = self._get_entity_name(author_entity)
        original_fwd_tag, _ = self._get_original_author_details(replied_message.fwd_from)

        # Create a short snippet of the replied message's content
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

        # Combine author name and snippet into the final quote text
        quote_text = f"{author_name}\n\u200b{quote_snippet}"
        entities = ArrayList()
        
        # Add formatting entities (bold, link) for the author name
        if isinstance(author_entity, TLRPC.TL_user):
            self._add_user_entities(entities, quote_text, author_entity, author_name)
        else:
            bold_entity = TLRPC.TL_messageEntityBold()
            bold_entity.offset, bold_entity.length = 0, self._get_java_len(author_name)
            entities.add(bold_entity)

        # Add the main blockquote entity that covers the entire text
        quote_entity = TLRPC.TL_messageEntityBlockquote()
        quote_entity.offset, quote_entity.length = 0, self._get_java_len(quote_text)
        entities.add(quote_entity)

        return quote_text, entities

    def _build_forward_header(self, message, source_entity, author_entity):
        """Builds a formatted header string (e.g., "Forwarded from...") for copied messages."""
        is_channel = isinstance(source_entity, TLRPC.TL_channel) and not getattr(source_entity, 'megagroup', False)
        is_group = isinstance(source_entity, TLRPC.TL_chat) or (isinstance(source_entity, TLRPC.TL_channel) and getattr(source_entity, 'megagroup', True))
        if is_channel: return self._build_channel_header(message, source_entity)
        if is_group: return self._build_group_header(message, source_entity, author_entity)
        me = get_user_config().getCurrentUser()
        sender, receiver = (author_entity, source_entity) if message.out else (author_entity, me)
        return self._build_private_header(message, sender, receiver)

    def _build_channel_header(self, message, channel):
        """Builds a header for messages from a channel."""
        name, entities = self._get_entity_name(channel), ArrayList()
        original_author_name, _ = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {name}"
        if original_author_name: text += f" (fwd_from {original_author_name})"
        link = TLRPC.TL_messageEntityTextUrl()
        link.offset, link.length = text.find(name), self._get_java_len(name)
        msg_id = message.fwd_from.channel_post if message.fwd_from and message.fwd_from.channel_post else message.id
        link.url = f"https://t.me/{channel.username}/{msg_id}" if channel.username else f"https://t.me/c/{channel.id}/{msg_id}"
        entities.add(link)
        return text, entities

    def _build_group_header(self, message, group, author):
        """Builds a header for messages from a group."""
        group_name, author_name, entities = self._get_entity_name(group), self._get_entity_name(author), ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {group_name} (by {author_name})"
        if original_author_name: text += f" fwd_from {original_author_name}"
        if isinstance(group, TLRPC.TL_channel): # Supergroups are channels
            msg_id = message.id
            group_link = f"https://t.me/{group.username}/{msg_id}" if group.username else f"https://t.me/c/{group.id}/{msg_id}"
            link_entity = TLRPC.TL_messageEntityTextUrl(); link_entity.offset, link_entity.length, link_entity.url = text.find(group_name), self._get_java_len(group_name), group_link
            entities.add(link_entity)
        else: # Regular groups are just bolded
            bold = TLRPC.TL_messageEntityBold(); bold.offset, bold.length = text.find(group_name), self._get_java_len(group_name)
            entities.add(bold)
        if author and isinstance(author, TLRPC.TL_user): self._add_user_entities(entities, text, author, author_name)
        if original_author_entity and isinstance(original_author_entity, TLRPC.TL_user): self._add_user_entities(entities, text, original_author_entity, original_author_name)
        return text, entities

    def _build_private_header(self, message, sender, receiver):
        """Builds a header for messages from a private chat."""
        sender_name, receiver_name, entities = self._get_entity_name(sender), self._get_entity_name(receiver), ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {sender_name} to {receiver_name}"
        if original_author_name: text += f" (original fwd_from {original_author_name})"
        for entity, name in [(sender, sender_name), (receiver, receiver_name), (original_author_entity, original_author_name)]:
            if entity and isinstance(entity, TLRPC.TL_user): self._add_user_entities(entities, text, entity, name)
        return text, entities

    # --- UI & Dialog Methods ---
    def create_settings(self) -> list:
        """Creates the list of UI components for the main plugin settings screen."""
        self._load_configurable_settings()
        self._load_forwarding_rules()
        settings_ui = [
            Header(text="General Settings"),
            Input(key="min_msg_length", text="Minimum Message Length", default=str(DEFAULT_SETTINGS["min_msg_length"]), subtext="For text-only messages."),
            Input(key="max_msg_length", text="Maximum Message Length", default=str(DEFAULT_SETTINGS["max_msg_length"]), subtext="For text-only messages."),
            Input(key="deferral_timeout_ms", text="Media Deferral Timeout (ms)", default=str(DEFAULT_SETTINGS["deferral_timeout_ms"]), subtext="Safety net for slow media downloads. Increase if files fail to send."),
            Input(key="album_timeout_ms", text="Album Buffering Timeout (ms)", default=str(DEFAULT_SETTINGS["album_timeout_ms"]), subtext="How long to wait for all media in an album before sending."),
            Input(key="deduplication_window_seconds", text="Deduplication Window (Seconds)", default=str(DEFAULT_SETTINGS["deduplication_window_seconds"]), subtext="Time window to ignore duplicate events and identical files."),
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
                style = "(Copy)" # This mode primarily copies
                settings_ui.append(Text(
                    text=f"From: {source_name}\nTo: {dest_name} {style}",
                    icon="msg_edit",
                    on_click=lambda v, sid=source_id: self._show_rule_action_dialog(sid)
                ))
        settings_ui.append(Divider())
        settings_ui.extend([
            Header(text="About & Support"),
            Text(text="TON", icon="msg_ton", accent=True, on_click=lambda view: self._copy_to_clipboard(self.TON_ADDRESS, "TON")),
            Text(text="USDT (TRC20)", icon="msg_copy", accent=True, on_click=lambda view: self._copy_to_clipboard(self.USDT_ADDRESS, "USDT")),
            Divider(),
            Text(text="Disclaimer & FAQ", icon="msg_help", accent=True, on_click=lambda v: self._show_faq_dialog()),
            Divider(),
            Text(
                text="Check for Updates",
                icon="msg_update",
                accent=True,
                on_click=lambda v: self.check_for_updates(is_manual=True)
            )
        ])
        return settings_ui

    def _add_chat_menu_item(self):
        """Adds the 'Auto Forward...' option to the chat three-dots menu."""
        self.add_menu_item(MenuItemData(menu_type=MenuItemType.CHAT_ACTION_MENU, text="Auto Forward...", icon="msg_forward", on_click=self._on_menu_item_click))

    def _on_menu_item_click(self, context):
        """Handles clicks on the 'Auto Forward...' menu item."""
        current_chat_id = context.get("dialog_id")
        if not current_chat_id: return
        current_chat_id = int(current_chat_id)
        # If a rule exists, show management options. Otherwise, show the creation dialog.
        if current_chat_id in self.forwarding_rules:
            run_on_ui_thread(lambda: self._show_rule_action_dialog(current_chat_id))
        else:
            source_name = self._get_chat_name(current_chat_id)
            run_on_ui_thread(lambda: self._show_destination_input_dialog(current_chat_id, source_name))

    def _show_rule_action_dialog(self, source_id):
        """Shows a dialog to Modify, Cancel, or Delete an existing rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Manage Rule")
        builder.set_message(f"What would you like to do with the rule for '{self._get_chat_name(source_id)}'?")
        builder.set_positive_button("Modify", lambda b, w: self._launch_modification_dialog(source_id))
        builder.set_neutral_button("Cancel", lambda b, w: b.dismiss())
        builder.set_negative_button("Delete", lambda b, w: self._delete_rule_with_confirmation(source_id))
        run_on_ui_thread(builder.show)

    def _launch_modification_dialog(self, source_id):
        """Launches the main settings dialog to modify an existing rule."""
        rule_data = self.forwarding_rules.get(source_id)
        if not rule_data:
            BulletinHelper.show_error("Could not find rule to modify.", get_last_fragment())
            return
        source_name = self._get_chat_name(source_id)
        run_on_ui_thread(lambda: self._show_destination_input_dialog(source_id, source_name, existing_rule=rule_data))
            
    def _show_destination_input_dialog(self, source_id, source_name, existing_rule=None):
        """Shows the main, complex dialog for creating or editing a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            title = f"Modify Rule for '{source_name}'" if existing_rule else f"Set Destination for '{source_name}'"
            builder.set_title(title)
    
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))
    
            scroller = ScrollView(activity)
            main_layout = LinearLayout(activity)
            main_layout.setOrientation(LinearLayout.VERTICAL)
            main_layout.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 4)
    
            # --- Section: Destination Input ---
            set_by_reply_button = TextView(activity)
            input_field = EditText(activity)
            
            set_by_reply_button.setText("Set by Replying")
            set_by_reply_button.setTextColor(Theme.getColor(Theme.key_dialogTextLink))
            set_by_reply_button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            set_by_reply_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            set_by_reply_params.setMargins(margin_px, margin_px // 4, margin_px, 0)
            set_by_reply_button.setLayoutParams(set_by_reply_params)
            main_layout.addView(set_by_reply_button)
    
            input_field.setHint("Destination Link, @username, or ID")
            input_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            input_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            input_field_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            input_field_params.setMargins(margin_px, margin_px // 4, margin_px, 0)
            input_field.setLayoutParams(input_field_params)
            main_layout.addView(input_field)

            # --- Section: Main Filters ---
            keyword_filter_input = EditText(activity)
            keyword_filter_input.setHint("Keyword/Regex Filter (optional)")
            keyword_filter_input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            keyword_filter_input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            keyword_filter_input_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            keyword_filter_input_params.setMargins(margin_px, margin_px // 4, margin_px, margin_px // 2)
            keyword_filter_input.setLayoutParams(keyword_filter_input_params)
            main_layout.addView(keyword_filter_input)
    
            checkbox_tint_list = ColorStateList([[-16842912], [16842912]], [Theme.getColor(Theme.key_checkbox), Theme.getColor(Theme.key_checkboxCheck)])
            checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            checkbox_params.setMargins(margin_px, 0, margin_px, 0)
    
            drop_author_checkbox = CheckBox(activity)
            drop_author_checkbox.setText("Remove Original Author (Copy)")
            drop_author_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); drop_author_checkbox.setButtonTintList(checkbox_tint_list)
            drop_author_checkbox.setLayoutParams(checkbox_params); main_layout.addView(drop_author_checkbox)
    
            quote_replies_checkbox = CheckBox(activity)
            quote_replies_checkbox.setText("Quote Replies")
            quote_replies_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); quote_replies_checkbox.setButtonTintList(checkbox_tint_list)
            quote_replies_checkbox.setLayoutParams(checkbox_params); main_layout.addView(quote_replies_checkbox)
    
            # --- Section: Topic Forwarding ---
            forward_to_topic_checkbox = CheckBox(activity)
            forward_to_topic_checkbox.setText("Forward to Topic / Comment Thread")
            forward_to_topic_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); forward_to_topic_checkbox.setButtonTintList(checkbox_tint_list)
            forward_to_topic_checkbox.setLayoutParams(checkbox_params); main_layout.addView(forward_to_topic_checkbox)
    
            topic_id_input = EditText(activity)
            topic_id_input.setHint("Topic ID (use Set by Replying)")
            topic_id_input.setInputType(InputType.TYPE_CLASS_NUMBER)
            topic_id_input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); topic_id_input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            topic_id_input_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            topic_id_input_params.setMargins(margin_px * 2, 0, margin_px, margin_px // 4)
            topic_id_input.setLayoutParams(topic_id_input_params)
            topic_id_input.setVisibility(View.GONE) # Hidden by default
            main_layout.addView(topic_id_input)
    
            # Listener to show/hide the Topic ID input field
            class TopicCheckboxListener(dynamic_proxy(CompoundButton.OnCheckedChangeListener)):
                def __init__(self, input_field): super().__init__(); self.input_field = input_field
                def onCheckedChanged(self, buttonView, isChecked):
                    self.input_field.setVisibility(View.VISIBLE if isChecked else View.GONE)
            forward_to_topic_checkbox.setOnCheckedChangeListener(TopicCheckboxListener(topic_id_input))
    
            # --- Section: Author Filtering ---
            divider_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 1); vertical_margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 12, activity.getResources().getDisplayMetrics()))
            divider_params.setMargins(margin_px, vertical_margin_px, margin_px, vertical_margin_px)
            divider_one = View(activity); divider_one.setBackgroundColor(Theme.getColor(Theme.key_divider)); divider_one.setLayoutParams(divider_params); main_layout.addView(divider_one)
    
            author_header = TextView(activity)
            author_header.setText("Forward messages from:")
            author_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); author_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            author_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            author_header_params.setMargins(margin_px, 0, margin_px, margin_px // 4); author_header.setLayoutParams(author_header_params); main_layout.addView(author_header)
    
            forward_users_checkbox = CheckBox(activity)
            forward_users_checkbox.setText("Users"); forward_users_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_users_checkbox.setButtonTintList(checkbox_tint_list); forward_users_checkbox.setLayoutParams(checkbox_params); main_layout.addView(forward_users_checkbox)
    
            forward_bots_checkbox = CheckBox(activity)
            forward_bots_checkbox.setText("Bots"); forward_bots_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_bots_checkbox.setButtonTintList(checkbox_tint_list); forward_bots_checkbox.setLayoutParams(checkbox_params); main_layout.addView(forward_bots_checkbox)
    
            forward_outgoing_checkbox = CheckBox(activity)
            forward_outgoing_checkbox.setText("Your Outgoing Messages"); forward_outgoing_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_outgoing_checkbox.setButtonTintList(checkbox_tint_list); forward_outgoing_checkbox.setLayoutParams(checkbox_params); main_layout.addView(forward_outgoing_checkbox)

            author_filter_input = EditText(activity)
            author_filter_input.setHint("Filter by Author ID/@user (optional, CSV)")
            author_filter_input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); author_filter_input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            author_filter_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            author_filter_params.setMargins(margin_px, 0, margin_px, margin_px // 2); author_filter_input.setLayoutParams(author_filter_params); main_layout.addView(author_filter_input)
    
            def update_author_filter_visibility():
                is_visible = forward_users_checkbox.isChecked() or forward_bots_checkbox.isChecked()
                author_filter_input.setVisibility(View.VISIBLE if is_visible else View.GONE)
    
            class AuthorCheckboxListener(dynamic_proxy(CompoundButton.OnCheckedChangeListener)):
                def __init__(self, update_func): super().__init__(); self.update_func = update_func
                def onCheckedChanged(self, buttonView, isChecked): self.update_func()
    
            listener = AuthorCheckboxListener(update_author_filter_visibility)
            forward_users_checkbox.setOnCheckedChangeListener(listener); forward_bots_checkbox.setOnCheckedChangeListener(listener)
    
            # --- Section: Content Type Filtering ---
            divider_two = View(activity); divider_two.setBackgroundColor(Theme.getColor(Theme.key_divider)); divider_two.setLayoutParams(divider_params); main_layout.addView(divider_two)
    
            filter_header = TextView(activity)
            filter_header.setText("Content to forward:")
            filter_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack)); filter_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            filter_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            filter_header_params.setMargins(margin_px, 0, margin_px, 0); filter_header.setLayoutParams(filter_header_params); main_layout.addView(filter_header)
    
            filter_checkboxes = {}
            for key, label in FILTER_TYPES.items():
                cb = CheckBox(activity); cb.setText(label); cb.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                cb.setButtonTintList(checkbox_tint_list); cb.setLayoutParams(checkbox_params)
                main_layout.addView(cb); filter_checkboxes[key] = cb
    
            # --- Pre-fill dialog if editing an existing rule ---
            if existing_rule:
                dest_entity = self._get_chat_entity(existing_rule.get("destination", 0))
                input_field.setText(f"@{dest_entity.username}" if dest_entity and hasattr(dest_entity, 'username') and dest_entity.username else str(existing_rule.get("destination", 0)))
    
                existing_topic_id = existing_rule.get("destination_topic_id", 0)
                if existing_topic_id > 0:
                    forward_to_topic_checkbox.setChecked(True)
                    topic_id_input.setVisibility(View.VISIBLE)
                    topic_id_input.setText(str(existing_topic_id))
    
                keyword_filter_input.setText(existing_rule.get("keyword_pattern", "")); author_filter_input.setText(existing_rule.get("author_filter", ""))
                drop_author_checkbox.setChecked(existing_rule.get("drop_author", True)); quote_replies_checkbox.setChecked(existing_rule.get("quote_replies", True))
                forward_users_checkbox.setChecked(existing_rule.get("forward_users", True)); forward_bots_checkbox.setChecked(existing_rule.get("forward_bots", True))
                forward_outgoing_checkbox.setChecked(existing_rule.get("forward_outgoing", True))
                for key, cb in filter_checkboxes.items(): cb.setChecked(existing_rule.get("filters", {}).get(key, True))
            else: # Default values for a new rule
                drop_author_checkbox.setChecked(False); quote_replies_checkbox.setChecked(True)
                forward_users_checkbox.setChecked(True); forward_bots_checkbox.setChecked(True); forward_outgoing_checkbox.setChecked(True)
                for cb in filter_checkboxes.values(): cb.setChecked(True)
    
            update_author_filter_visibility()
            scroller.addView(main_layout)
            builder.set_view(scroller)
    
            # --- Dialog Button Actions ---
            def on_set_click(d, w):
                topic_id_str = topic_id_input.getText().toString()
                topic_id = int(topic_id_str) if forward_to_topic_checkbox.isChecked() and topic_id_str.isdigit() else 0
                filter_settings = {key: cb.isChecked() for key, cb in filter_checkboxes.items()}
                self._process_destination_input(
                    source_id, source_name, input_field.getText().toString(),
                    keyword_filter_input.getText().toString(), author_filter_input.getText().toString(),
                    drop_author_checkbox.isChecked(), quote_replies_checkbox.isChecked(),
                    forward_to_topic_checkbox.isChecked(), topic_id,
                    forward_users_checkbox.isChecked(), forward_bots_checkbox.isChecked(),
                    forward_outgoing_checkbox.isChecked(), filter_settings)
    
            builder.set_positive_button("Set", on_set_click)
            builder.set_negative_button("Cancel", lambda d, w: d.dismiss())
            dialog = builder.create()
    
            all_ui_elements = {
                'input_field': input_field, 'keyword_filter_input': keyword_filter_input,
                'drop_author_checkbox': drop_author_checkbox, 'quote_replies_checkbox': quote_replies_checkbox,
                'forward_to_topic_checkbox': forward_to_topic_checkbox, 'topic_id_input': topic_id_input,
                'author_filter_input': author_filter_input, 'forward_users_checkbox': forward_users_checkbox,
                'forward_bots_checkbox': forward_bots_checkbox, 'forward_outgoing_checkbox': forward_outgoing_checkbox,
                'filter_checkboxes': filter_checkboxes
            }
            on_reply_click_callback = lambda v: self._show_set_by_replying_prompt(activity, dialog, source_id, source_name, all_ui_elements)
            set_by_reply_button.setOnClickListener(self.OnClickListenerProxy(on_reply_click_callback))
            
            run_on_ui_thread(dialog.show)
        except Exception:
            log(f"[{self.id}] ERROR showing rule setup dialog: {traceback.format_exc()}")

    def _show_set_by_replying_prompt(self, activity, main_dialog, source_id, source_name, ui_elements):
        """Shows the prompt instructing the user how to use the 'Set by Replying' feature."""
        builder = AlertDialogBuilder(activity)
        builder.set_title("Set Destination by Replying")
        builder.set_message("Click 'Proceed', then go to your desired destination chat (or topic) and REPLY to ANY message with the exact word 'set'. The reply will be auto-deleted.")
        
        def on_proceed(b, w):
            # Capture all settings from the UI before starting the listener
            rule_settings = {
                "keyword_pattern": ui_elements['keyword_filter_input'].getText().toString(),
                "author_filter": ui_elements['author_filter_input'].getText().toString(),
                "drop_author": ui_elements['drop_author_checkbox'].isChecked(),
                "quote_replies": ui_elements['quote_replies_checkbox'].isChecked(),
                "forward_to_topic": ui_elements['forward_to_topic_checkbox'].isChecked(),
                "destination_topic_id": 0, # This will be detected automatically
                "forward_users": ui_elements['forward_users_checkbox'].isChecked(),
                "forward_bots": ui_elements['forward_bots_checkbox'].isChecked(),
                "forward_outgoing": ui_elements['forward_outgoing_checkbox'].isChecked(),
                "filter_settings": {key: cb.isChecked() for key, cb in ui_elements['filter_checkboxes'].items()}
            }
            
            self._start_reply_listening(source_id, source_name, rule_settings)
            main_dialog.dismiss()
            b.dismiss()

        builder.set_positive_button("Proceed", on_proceed)
        builder.set_negative_button("Cancel", None)
        run_on_ui_thread(builder.show)

    class ReplyListenerTimeoutTask(dynamic_proxy(Runnable)):
        """A proxy class to handle the timeout for the reply listener."""
        def __init__(self, plugin):
            super().__init__()
            self.plugin = plugin
        def run(self):
            self.plugin._on_reply_listener_timeout()

    def _start_reply_listening(self, source_id, source_name, rule_settings):
        """Activates the listening state for the 'set' reply."""
        activity = get_last_fragment().getParentActivity()
        if self.is_listening_for_reply:
            if activity: BulletinHelper.show_info("Already listening for a reply.", get_last_fragment())
            return
        
        self.is_listening_for_reply = True
        self.reply_listener_context = {
            'source_id': source_id,
            'source_name': source_name,
            'rule_settings': rule_settings,
            'activity': activity
        }
        self.reply_listener_timeout_task = self.ReplyListenerTimeoutTask(self)
        self.handler.postDelayed(self.reply_listener_timeout_task, 60000)
        if activity: BulletinHelper.show_info("Listening... reply with 'set' in the destination chat.", get_last_fragment())
        
    def _on_reply_listener_timeout(self):
        """Called if the user does not reply with 'set' within the time limit."""
        if self.is_listening_for_reply:
            self.is_listening_for_reply = False
            context = self.reply_listener_context
            self.reply_listener_context = {}
            self.reply_listener_timeout_task = None
            activity = context.get('activity')
            if activity:
                run_on_ui_thread(lambda: BulletinHelper.show_error("Timed out. No reply detected.", get_last_fragment()))

    def _process_reply_trigger(self, message_object):
        """
        Handles the logic after a 'set' message is detected.
        This now works for both replies and direct messages sent to a topic.
        """
        try:
            msg = message_object.messageOwner

            # We can now proceed. Stop the listener and cancel the timeout.
            self.is_listening_for_reply = False
            if self.reply_listener_timeout_task:
                self.handler.removeCallbacks(self.reply_listener_timeout_task)
                self.reply_listener_timeout_task = None

            context = self.reply_listener_context
            rule_settings = context.get('rule_settings')
            
            dest_id = msg.dialog_id
            dest_name = self._get_chat_name(dest_id)
            
            detected_topic_id = 0
            # A message sent to a topic (or as a reply) will have a 'reply_to' header.
            if hasattr(msg, 'reply_to') and msg.reply_to:
                reply_header = msg.reply_to
                
                # Priority 1: Modern "Forum Topics" have a 'reply_to_top_id'.
                if hasattr(reply_header, 'reply_to_top_id') and reply_header.reply_to_top_id != 0:
                    detected_topic_id = reply_header.reply_to_top_id
                # Priority 2: Fallback for "Comment Threads" which are anchored to a message ID.
                elif hasattr(reply_header, 'reply_to_msg_id'):
                    detected_topic_id = reply_header.reply_to_msg_id

            if detected_topic_id > 0 and rule_settings is not None:
                rule_settings["destination_topic_id"] = detected_topic_id

            # Finalize the rule with all the discovered information.
            self._finalize_rule(
                context.get('source_id'),
                context.get('source_name'),
                dest_id,
                dest_name,
                rule_settings
            )
            
            # Auto-delete the 'set' message to keep the chat clean.
            self._delete_message_by_id(msg.dialog_id, msg.id)
            
            self.reply_listener_context = {}

        except Exception:
            log(f"[{self.id}] ERROR in _process_reply_trigger: {traceback.format_exc()}")
            self.is_listening_for_reply = False

    # --- Rule Processing and Resolution ---
    def _process_destination_input(self, source_id, source_name, user_input, *args):
        """Processes the destination provided manually in the settings dialog."""
        (keyword_pattern, author_filter, drop_author, quote_replies, forward_to_topic, 
         topic_id, forward_users, forward_bots, forward_outgoing, filter_settings) = args

        cleaned_input = (user_input or "").strip()
        if not cleaned_input: 
            BulletinHelper.show_error("Destination cannot be empty.")
            return

        rule_settings = {
            "keyword_pattern": keyword_pattern, "author_filter": author_filter, "drop_author": drop_author, 
            "quote_replies": quote_replies, "forward_to_topic": forward_to_topic, "destination_topic_id": topic_id,
            "forward_users": forward_users, "forward_bots": forward_bots, 
            "forward_outgoing": forward_outgoing, "filter_settings": filter_settings
        }

        # Route the input to the correct resolver based on its format.
        if "/joinchat/" in cleaned_input or "/+" in cleaned_input:
            self._resolve_as_invite_link(cleaned_input, source_id, source_name, rule_settings)
            return
        
        try:
            input_as_int = int(cleaned_input)
            cached_entity = self._get_chat_entity_from_input_id(input_as_int)
            if cached_entity:
                self._finalize_rule(source_id, source_name, self._get_id_for_storage(cached_entity), self._get_entity_name(cached_entity), rule_settings)
                return
            # If not in cache, try a network request.
            self._resolve_by_id_shotgun(input_as_int, source_id, source_name, rule_settings)
        except ValueError:
            # If it's not a number, treat it as a username or public link.
            self._resolve_as_username(cleaned_input, source_id, source_name, rule_settings)

    def _resolve_as_invite_link(self, cleaned_input, source_id, source_name, rule_settings):
        """Resolves a destination using a t.me/joinchat/... or t.me/+... link."""
        try:
            hash_val = cleaned_input.split("/")[-1]
            req = TLRPC.TL_messages_checkChatInvite(); req.hash = hash_val
            
            def on_check_invite(response, error):
                if error or not response or not hasattr(response, 'chat'):
                    error_text = getattr(error, 'text', 'Invalid or expired link')
                    BulletinHelper.show_error(f"Failed to resolve link: {error_text}", get_last_fragment())
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
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}. Reason: {error_text}", get_last_fragment())
                return
            
            dest_entity = response.chats.get(0)
            if dest_entity:
                get_messages_controller().putChat(dest_entity, True)
                dest_id = self._get_id_for_storage(dest_entity)
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            else:
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}", get_last_fragment())

        # The API for getting a chat by ID is tricky, so we try a few common variations.
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
        """Resolver for public links (t.me/...) and @usernames."""
        log(f"[{self.id}] Resolving '{username}' as a username/public link.")
        
        def on_resolve_complete(response, error):
            if error or not response:
                error_text = getattr(error, 'text', 'Not found')
                BulletinHelper.show_error(f"Could not resolve '{username}': {error_text}", get_last_fragment())
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
                BulletinHelper.show_error(f"Could not resolve '{username}'.", get_last_fragment())
        
        try:
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = username.replace("@", "").split("/")[-1]
            send_request(req, RequestCallback(on_resolve_complete))
        except Exception:
            log(f"[{self.id}] ERROR resolving username: {traceback.format_exc()}")

    def _finalize_rule(self, source_id, source_name, destination_id, dest_name, rule_settings):
        """Saves the final, resolved rule to storage and notifies the user."""
        if destination_id == 0:
            log(f"[{self.id}] Finalize rule called with invalid destination_id=0. Aborting.")
            BulletinHelper.show_error("Failed to save rule: Invalid destination chat resolved.", get_last_fragment())
            return
    
        topic_id = rule_settings.get("destination_topic_id", 0)
    
        rule_data = {
            "destination": destination_id,
            "enabled": True,
            "drop_author": rule_settings["drop_author"],
            "quote_replies": rule_settings["quote_replies"],
            "destination_topic_id": topic_id,
            "keyword_pattern": rule_settings["keyword_pattern"],
            "author_filter": rule_settings["author_filter"],
            "forward_users": rule_settings["forward_users"],
            "forward_bots": rule_settings["forward_bots"],
            "forward_outgoing": rule_settings["forward_outgoing"],
            "filters": rule_settings["filter_settings"]
        }
        log(f"[{self.id}] Finalizing rule. Saving topic ID: {topic_id}")
    
        self.forwarding_rules[source_id] = rule_data
        self._save_forwarding_rules()
        BulletinHelper.show_info(f"Rule saved: '{source_name}' → '{dest_name}'", get_last_fragment())

    def _delete_rule_with_confirmation(self, source_id):
        """Shows a confirmation dialog before deleting a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Delete Rule?")
            builder.set_message(f"Are you sure you want to delete the rule for '{self._get_chat_name(source_id)}'?")
            builder.set_positive_button("Delete", lambda b, w: self._execute_delete(source_id))
            builder.set_negative_button("Cancel", None)
            run_on_ui_thread(builder.show)
        except Exception: log(f"[{self.id}] ERROR in delete confirmation: {traceback.format_exc()}")

    def _execute_delete(self, source_id):
        """Performs the actual deletion of a rule."""
        if source_id in self.forwarding_rules:
            source_name = self._get_chat_name(source_id)
            del self.forwarding_rules[source_id]
            self._save_forwarding_rules()
            BulletinHelper.show_info(f"Rule for '{source_name}' deleted.", get_last_fragment())
            self._refresh_settings_ui()

    # --- Telegram API Utilities ---
    def _delete_message_by_id(self, chat_id, message_id):
        """Reliably deletes a single message by its ID."""
        try:
            id_list = ArrayList()
            id_list.add(Integer(message_id))
            channel_id = 0
            # The controller needs a specific channel_id format for supergroups.
            if str(chat_id).startswith("-100"):
                channel_id = int(str(chat_id)[4:])
            get_messages_controller().deleteMessages(id_list, None, None, chat_id, 0, True, channel_id)
            log(f"[{self.id}] Delete command sent for message {message_id} in chat {chat_id}.")
        except Exception:
            log(f"[{self.id}] ERROR in _delete_message_by_id: {traceback.format_exc()}")
            
    def _is_media_complete(self, message):
        """Checks if a message's media has a file reference, indicating it's ready to forward."""
        if not message or not hasattr(message, 'media') or not message.media:
            return True # Not media, so it's "complete"
        if hasattr(message.media, 'photo') and getattr(message.media.photo, 'file_reference', None):
            return True
        if hasattr(message.media, 'document') and getattr(message.media.document, 'file_reference', None):
            return True
        return False
        
    def _get_document_filename(self, doc):
        """Extracts the filename from a document's attributes."""
        if not doc or not hasattr(doc, 'attributes') or not doc.attributes:
            return None
        try:
            for i in range(doc.attributes.size()):
                attr = doc.attributes.get(i)
                if isinstance(attr, TLRPC.TL_documentAttributeFilename):
                    return attr.file_name
        except Exception as e:
            log(f"[{self.id}] ERROR: Could not get filename from doc attributes. Error: {e}")
        return None

    def _get_author_type(self, message):
        """Determines if a message was sent by a user, a bot, or is outgoing."""
        if message.out:
            return "outgoing"
        author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
        if author_entity and getattr(author_entity, 'bot', False):
            return "bot"
        return "user"

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
        """Checks if a given text matches a keyword or regex pattern."""
        if not pattern:
            return True
        if not text_to_check:
            return False
        try:
            # Try to compile as regex first for advanced matching.
            compiled_regex = re.compile(pattern, re.IGNORECASE)
            if compiled_regex.search(text_to_check):
                return True
        except re.error:
            # If regex fails, fall back to simple substring matching.
            if pattern.lower() in text_to_check.lower():
                return True
        return False

    def _get_java_len(self, py_string: str) -> int:
        """Gets the length of a Python string as Java would see it, crucial for entity offsets."""
        if not py_string:
            return 0
        return JavaString(py_string).length()

    def _add_user_entities(self, entities: ArrayList, text: str, user_entity: TLRPC.TL_user, display_name: str):
        """Adds bold and clickable user link entities to a message."""
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

    def _get_input_media(self, message_object):
        """Converts a message's media into the correct InputMedia format for sending."""
        media = getattr(message_object.messageOwner, "media", None)
        if not media: return None
        try:
            if isinstance(media, TLRPC.TL_messageMediaPhoto) and hasattr(media, "photo"):
                photo = media.photo
                input_media = TLRPC.TL_inputMediaPhoto()
                input_media.id = TLRPC.TL_inputPhoto()
                input_media.id.id, input_media.id.access_hash = photo.id, photo.access_hash
                input_media.id.file_reference = photo.file_reference or bytearray(0)
                return input_media
            if isinstance(media, TLRPC.TL_messageMediaDocument) and hasattr(media, "document"):
                doc = media.document
                input_media = TLRPC.TL_inputMediaDocument()
                input_media.id = TLRPC.TL_inputDocument()
                input_media.id.id, input_media.id.access_hash = doc.id, doc.access_hash
                input_media.id.file_reference = doc.file_reference or bytearray(0)
                return input_media
        except Exception:
            log(f"[{self.id}] Failed to get input media: {traceback.format_exc()}")
        return None

    def _prepare_final_entities(self, prefix_text, prefix_entities, original_entities):
        """Combines prefix entities with original message entities, adjusting offsets correctly."""
        final_entities = ArrayList()
        if prefix_entities: final_entities.addAll(prefix_entities)
        if original_entities and not original_entities.isEmpty():
            # The offset needs to account for the length of the prefix and the two newlines.
            offset_shift = self._get_java_len(prefix_text) + 2 if prefix_text else 0
            for i in range(original_entities.size()):
                old = original_entities.get(i)
                # Re-create the entity to avoid modifying the original
                new = type(old)()
                new.offset, new.length = old.offset + offset_shift, old.length
                if hasattr(old, 'url'): new.url = old.url
                if hasattr(old, 'user_id'): new.user_id = old.user_id
                final_entities.add(new)
        return final_entities

    def _get_id_from_peer(self, peer):
        """Utility to extract a numeric ID from a Peer object."""
        if not peer: return 0
        if isinstance(peer, TLRPC.TL_peerChannel): return -peer.channel_id
        if isinstance(peer, TLRPC.TL_peerChat): return -peer.chat_id
        if isinstance(peer, TLRPC.TL_peerUser): return peer.user_id
        return 0

    def _get_id_for_storage(self, entity):
        """Utility to get the correct ID format for storage/requests from a User/Chat entity."""
        if not entity: return 0
        return -entity.id if not isinstance(entity, TLRPC.TL_user) else entity.id

    def _get_chat_entity_from_input_id(self, input_id: int):
        """Gets a chat/user entity from the local cache using a numeric ID."""
        if input_id == 0: return None
        abs_id, controller = abs(input_id), get_messages_controller()
        entity = controller.getChat(abs_id)
        if entity: return entity
        if input_id > 0: return controller.getUser(input_id)
        return None

    def _sanitize_chat_id_for_request(self, input_id: int) -> int:
        """Sanitizes a supergroup ID for use in certain API requests."""
        id_str = str(abs(input_id))
        if id_str.startswith("100") and len(id_str) > 9:
            try: return int(id_str[3:])
            except (ValueError, IndexError): pass
        return abs(input_id)

    def _get_chat_entity(self, dialog_id):
        """Gets a user or chat entity object from a dialog ID."""
        if not isinstance(dialog_id, int):
            try: dialog_id = int(dialog_id)
            except (ValueError, TypeError): return None
        return get_messages_controller().getUser(dialog_id) if dialog_id > 0 else get_messages_controller().getChat(abs(dialog_id))

    def _get_entity_name(self, entity):
        """Gets a display-friendly name from a user or chat entity."""
        if not entity: return "Unknown"
        if hasattr(entity, 'title'): return entity.title
        if hasattr(entity, 'first_name'):
            name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
            return name if name else f"ID: {entity.id}"
        return f"ID: {getattr(entity, 'id', 'N/A')}"

    def _get_chat_name(self, chat_id):
        """Convenience function to get a chat name directly from a chat ID."""
        return self._get_entity_name(self._get_chat_entity(int(chat_id)))

    def _get_original_author_details(self, fwd_header):
        """Extracts author details from a fwd_from header."""
        if not fwd_header: return None, None
        original_author_name, original_author_entity = None, None
        original_author_id = self._get_id_from_peer(getattr(fwd_header, 'from_id', None))
        if original_author_id: original_author_entity = self._get_chat_entity(original_author_id)
        if original_author_entity: original_author_name = self._get_entity_name(original_author_entity)
        elif hasattr(fwd_header, 'from_name') and fwd_header.from_name: original_author_name = fwd_header.from_name
        return original_author_name, original_author_entity
    
    # --- Misc UI and Utilities ---
    def _refresh_settings_ui(self):
        """Forces the plugin settings screen to rebuild its views."""
        try:
            last_fragment = get_last_fragment()
            if isinstance(last_fragment, PluginSettingsActivity) and hasattr(last_fragment, 'rebuildViews'):
                run_on_ui_thread(last_fragment.rebuildViews)
        except Exception: log(f"[{self.id}] ERROR during UI refresh: {traceback.format_exc()}")

    def _copy_to_clipboard(self, text_to_copy: str, label: str):
        """Copies text to the clipboard and shows a toast notification."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
            clip = ClipData.newPlainText(label, text_to_copy)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(activity, f"{label} address copied to clipboard!", Toast.LENGTH_SHORT).show()
        except Exception: log(f"[{self.id}] Failed to copy to clipboard: {traceback.format_exc()}")

    def _process_changelog_markdown(self, text):
        """A simple markdown-to-HTML converter for the update dialog."""
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
            if not stripped: html_lines.append("") ; continue
            if stripped.startswith('### '): html_lines.append(f"<b>{process_inline(stripped[4:])}</b>")
            elif stripped.startswith('* '): html_lines.append(f"•&nbsp;&nbsp;{process_inline(stripped[2:])}")
            elif stripped.startswith('- '): html_lines.append(f"&nbsp;&nbsp;-&nbsp;&nbsp;{process_inline(stripped[2:])}")
            else: html_lines.append(process_inline(stripped))
        html_text = '<br>'.join(html_lines)
        return re.sub(r'(<br>\s*){2,}', '<br><br>', html_text)

    def _show_faq_dialog(self):
        """Displays the formatted FAQ and Disclaimer dialog."""
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
            
            # Simple markdown to HTML for the FAQ text
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
                if not stripped_line: html_lines.append(""); continue
                if stripped_line == '---': html_lines.append(f"<p align='center'><font color='{accent_color_hex}'>•&nbsp;•&nbsp;•</font></p>"); continue
                
                content_spoilers_processed = re.sub(r'\|\|(.*?)\|\|', rf'<font style="background-color:{spoiler_color_hex};color:{spoiler_color_hex};">&nbsp;\1&nbsp;</font>', stripped_line)
                if re.match(r'^\*\*(.*)\*\*$', stripped_line):
                    content = stripped_line.replace('**', '').strip()
                    html_lines.append(f"<b><font color='{accent_color_hex}'>{content}</font></b>")
                elif stripped_line.startswith('* '): html_lines.append(f"&nbsp;&nbsp;•&nbsp;&nbsp;<b>{process_inline_markdown(content_spoilers_processed[2:])}</b>")
                elif stripped_line.startswith('- '): html_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;{process_inline_markdown(content_spoilers_processed[2:])}")
                else: html_lines.append(process_inline_markdown(content_spoilers_processed))

            html_text = re.sub(r'(<br>\s*){2,}', '<br><br>', '<br>'.join(html_lines))
            # Use legacy mode for broader compatibility
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
            run_on_ui_thread(builder.show)
        except Exception:
            log(f"[{self.id}] ERROR showing FAQ dialog: {traceback.format_exc()}")

    # --- Update Mechanism ---
    def _updater_loop(self):
        """A background thread that periodically checks for new plugin updates."""
        log(f"[{self.id}] Updater loop started.")
        time.sleep(60) # Initial delay before first check
        while not self.stop_updater_thread.is_set():
            self.check_for_updates(is_manual=False)
            self.stop_updater_thread.wait(self.UPDATE_INTERVAL_SECONDS)
        log(f"[{self.id}] Updater loop finished.")

    def check_for_updates(self, is_manual=False):
        """Initiates an update check, optionally showing UI feedback."""
        if is_manual: BulletinHelper.show_info("Checking for updates...", get_last_fragment())
        threading.Thread(target=self._perform_update_check, args=[is_manual]).start()

    def _perform_update_check(self, is_manual):
        """Connects to the GitHub API to check for the latest release."""
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
                
                # Compare versions using tuples for correctness (e.g., 1.10.0 > 1.9.0)
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
                        BulletinHelper.show_error("Update found, but no download file available.", get_last_fragment())
                elif is_manual:
                    BulletinHelper.show_info("You are on the latest version!", get_last_fragment())
            elif is_manual:
                BulletinHelper.show_error(f"Failed to fetch updates (HTTP {connection.getResponseCode()})", get_last_fragment())
        except Exception as e:
            log(f"[{self.id}] Update check failed: {traceback.format_exc()}")
            if is_manual: BulletinHelper.show_error("Update check failed. See logs.", get_last_fragment())

    def _show_update_dialog(self, version, changelog, download_url):
        """Displays a dialog with changelog and an option to update."""
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
        run_on_ui_thread(builder.show)

    def _download_and_install(self, url, version):
        """Downloads the new plugin file and initiates the installation process."""
        try:
            BulletinHelper.show_info(f"Downloading update v{version}...", get_last_fragment())
            connection = URL(url).openConnection()
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
                        BulletinHelper.show_error(f"Update failed: {error_msg}", get_last_fragment())
                    else:
                        log(f"[{self.id}] Update to v{version} successful! Restart ExteraGram to apply.")
                        def close_settings_action():
                            fragment = get_last_fragment()
                            if fragment and hasattr(fragment, 'finishFragment'):
                                run_on_ui_thread(fragment.finishFragment)
                        BulletinHelper.show_with_button(f"Update v{version} installed! Please restart.", R.raw.chats_infotip, "DONE",
                            lambda: close_settings_action(), fragment=get_last_fragment())
                    if temp_file.exists():
                        temp_file.delete()
                
                install_callback_proxy = self.InstallCallback(on_install_callback)
                plugins_controller.loadPluginFromFile(temp_file.getAbsolutePath(), install_callback_proxy)
            else:
                BulletinHelper.show_error("Download failed.", get_last_fragment())
        except Exception:
            log(f"[{self.id}] Download and install failed: {traceback.format_exc()}")
            BulletinHelper.show_error("An error occurred during update.", get_last_fragment())

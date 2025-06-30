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
from java.util import ArrayList, HashSet
from android.content.res import ColorStateList
from android.content import ClipData, ClipboardManager, Context
from android.os import Handler, Looper
from java.lang import Runnable
from android.content import Intent
from android.net import Uri
from android.graphics import Typeface


# --- Telegram & Client Utilities ---
from org.telegram.messenger import NotificationCenter, MessageObject
from org.telegram.tgnet import TLRPC
from org.telegram.ui.ActionBar import Theme
from com.exteragram.messenger.plugins.ui import PluginSettingsActivity
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
__version__ = "1.0.1"
__min_version__ = "11.9.1"
__icon__ = "Putin_1337/14"

# --- Constants & Default Settings ---
# The key used for storing forwarding rules. Changing this will reset all user rules.
FORWARDING_RULES_KEY = "forwarding_rules_v1337"
DEFAULT_SETTINGS = {
    "deferral_timeout_ms": 5000,
    "min_msg_length": 1,
    "max_msg_length": 4096,
    "deduplication_window_seconds": 10.0,
    "album_timeout_ms": 800,
    "antispam_delay_seconds": 1.0
}

# Defines the available content types for filtering.
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

# A multi-line string containing the FAQ and disclaimer text.
# It uses a custom markdown-like syntax that is parsed into rich text.
FAQ_TEXT = """
---
**Disclaimer and Responsible Usage**
---
Please be aware that using a plugin like this automates actions on your personal Telegram account. This practice is often referred to as 'self-botting'.

This kind of automation may be considered a violation of [Telegram's Terms of Service](https://telegram.org/tos), which can prohibit bot-like activity from user accounts. Using this plugin carries potential risks, including account limitations or bans. You accept full responsibility for your actions. The author is not responsible for any consequences from your use or misuse of this tool. **Use at your own risk.**

---
**FAQ**
---
**🚀 Core Functionality**

* **How do I create a rule?**
    Go into any chat you want to forward messages *from*. Tap the three-dots menu (⋮) in the top right and select "Auto Forward...". A dialog will then ask for the destination chat.

* **How do I edit or delete a rule?**
    Go to a chat where a rule is active and open the "Auto Forward..." menu item again. A "Manage Rule" dialog will appear, allowing you to modify or delete it. You can also manage all rules from the main plugin settings page.

* **What's the difference between "Copy" and "Forward" mode?**
    When setting up a rule, you have a checkbox for "Remove Original Author".
    - **Checked (Copy Mode):** Sends a brand new message to the destination. It looks like you sent it yourself. All text formatting is preserved.
    - **Unchecked (Forward Mode):** Performs a standard Telegram forward, including the "Forwarded from..." header, preserving the original author's context.

* **Can I stop my own messages from being forwarded?**
    Yes. When creating or modifying a rule, uncheck the "Forward My Own Messages" option. This is useful if you only want to forward messages you *receive* in a chat, not those you send.

---
**✨ Advanced Features & Formatting**

* **How does the Anti-Spam Firewall work?**
    It's a rate-limiter that prevents a single user from flooding your destination chat. It works by enforcing a minimum time delay between forwards *from the same person*. You can configure this delay in the General Settings.

* **How do the content filters work?**
    When creating or modifying a rule, you'll see checkboxes for different message types (Text, Photos, Videos, etc.). Simply uncheck any content type you *don't* want to be forwarded for that specific rule. For example, you can set up a rule to forward only photos and videos from a channel, ignoring all text messages.

* **Does the plugin support text formatting (Markdown)?**
    Yes, completely. In 'Copy' mode, the plugin perfectly preserves all text formatting from the original message. This includes:
    - **Bold** and *italic* text
    - `Monospace code`
    - ~~Strikethrough~~ and __underline__
    - ||Spoilers||
    - [Custom Hyperlinks](https://telegram.org)
    - Mentions and #hashtags

---
**⚙️ Technical Settings & Troubleshooting**

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

    def __init__(self):
        super().__init__()
        self.id = __id__
        self.forwarding_rules = {}
        self.error_message = None
        self.deferred_messages = {}
        self.album_buffer = {}
        # A deque to store recent message keys for deduplication purposes.
        self.processed_keys = collections.deque(maxlen=200)
        # An Android Handler to schedule tasks on the main UI thread.
        self.handler = Handler(Looper.getMainLooper())
        # A cache to store the last message timestamp for each user, for the anti-spam firewall.
        self.user_last_message_time = collections.OrderedDict()
        self._load_configurable_settings()

    def on_plugin_load(self):
        """Called when the plugin is loaded. Registers the new message observer."""
        log(f"[{self.id}] Loading version {__version__}...")
        self._load_configurable_settings()
        self._load_forwarding_rules()
        self._add_chat_menu_item()
        account_instance = get_account_instance()
        if account_instance:
            account_instance.getNotificationCenter().addObserver(self, NotificationCenter.didReceiveNewMessages)

    def on_plugin_unload(self):
        """Called when the plugin is unloaded. Removes the observer and cancels any pending tasks."""
        account_instance = get_account_instance()
        if account_instance:
            account_instance.getNotificationCenter().removeObserver(self, NotificationCenter.didReceiveNewMessages)
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
        if id != NotificationCenter.didReceiveNewMessages: return
        try:
            if not self.forwarding_rules: return

            messages_list = args[1]
            for i in range(messages_list.size()):
                message_object = messages_list.get(i)
                if not (hasattr(message_object, 'messageOwner') and message_object.messageOwner): continue
                self.handle_message_event(message_object)
        except Exception:
            log(f"[{self.id}] ERROR in notification handler: {traceback.format_exc()}")

    def handle_message_event(self, message_object):
        """Main processing pipeline for each incoming message."""
        message = message_object.messageOwner
        
        # Step 1: Check if a rule exists for this chat and if it's enabled.
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule or not rule.get("enabled", False):
            return
    
        # --- CORRECTED LOGIC ORDER ---
        # Step 2: Album Handling. This must come BEFORE the anti-spam check.
        # We group all album parts first, so they don't trigger the rate limit against each other.
        grouped_id = getattr(message, 'grouped_id', 0)
        if grouped_id != 0:
            if grouped_id not in self.album_buffer:
                log(f"[{self.id}] Detected start of new album: {grouped_id}")
                album_task = AlbumTask(self, grouped_id)
                self.album_buffer[grouped_id] = {'messages': [], 'task': album_task}
                self.handler.postDelayed(album_task, self.album_timeout_ms)
            self.album_buffer[grouped_id]['messages'].append(message_object)
            return # IMPORTANT: We are done with this message part, it is now buffered.
    
        # Step 3: Anti-Spam Firewall. Now only applies to non-album messages.
        if self.antispam_delay_seconds > 0:
            author_id = get_user_config().getClientUserId() if message.out else self._get_id_from_peer(message.from_id)
            if author_id:
                current_time = time.time()
                last_time = self.user_last_message_time.get(author_id)
                
                if last_time and (current_time - last_time) < self.antispam_delay_seconds:
                    log(f"[{self.id}] Dropping message from user {author_id} due to anti-spam rate limit.")
                    return # Drop the message
                
                self.user_last_message_time[author_id] = current_time
                if len(self.user_last_message_time) > self.USER_TIMESTAMP_CACHE_SIZE:
                    self.user_last_message_time.popitem(last=False)
    
        # Step 4: Check per-rule setting for forwarding own messages.
        should_forward_own = rule.get("forward_own", True)
        if message.out and not should_forward_own:
            return
    
        # Step 5: Generate a stable, unique key for this message event for deduplication.
        event_key = None
        if message.out:
            event_key = ("outgoing", message.dialog_id, message.date, message.message or "")
        else:
            author_id = self._get_id_from_peer(message.from_id)
            event_key = ("incoming", author_id, source_chat_id, message.id)
    
        # Step 6: Deduplication.
        if any(key == event_key for key, ts in self.processed_keys):
            return
            
        # Step 7: Deferral logic for single messages.
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
    
        # Step 8: Final Processing.
        if event_key in self.deferred_messages:
            _, deferred_task = self.deferred_messages[event_key]
            self.handler.removeCallbacks(deferred_task)
            del self.deferred_messages[event_key]
                
        self.process_and_send(message_object, event_key)

    def _process_timed_out_message(self, event_key):
        """Processes a deferred message, re-fetching it from cache to ensure data is fresh."""
        if event_key in self.deferred_messages:
            log(f"[{self.id}] Processing deferred message after timeout. Key: {event_key}")
            message_object, _ = self.deferred_messages[event_key]
            
            final_message_object = message_object
            try:
                # Attempt to re-fetch the message from the main client cache.
                # This may provide a "hydrated" object with complete media info or the reply object.
                original_message = message_object.messageOwner
                if not original_message.out and hasattr(get_messages_controller(), 'getMessage'):
                    cached_message_obj = get_messages_controller().getMessage(original_message.dialog_id, original_message.id)
                    if cached_message_obj:
                        final_message_object = cached_message_obj
                        log(f"[{self.id}] Successfully re-fetched message from cache.")
            except Exception as e:
                log(f"[{self.id}] Could not re-fetch message from cache, proceeding with original object. Error: {e}")

            self.process_and_send(final_message_object, event_key)
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
            
        # Deduplication check for the whole album.
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
            return True # If no filters are defined, allow all.
        
        if message_object.isPhoto():
            return filters.get("photos", True)
        if message_object.isSticker():
            return filters.get("stickers", True)
        if message_object.isVoice():
            return filters.get("voice", True)
        if message_object.isRoundVideo():
            return filters.get("video_messages", True)
        if message_object.isGif():
            return filters.get("gifs", True)
        if message_object.isMusic():
            return filters.get("audio", True)
        if message_object.isVideo():
            return filters.get("videos", True)
        if message_object.isDocument():
            return filters.get("documents", True)

        # Default case for text messages.
        return filters.get("text", True)

    def process_and_send(self, message_object, event_key):
        """Final processing stage that applies all filters and sends the message."""
        # Deduplication check is repeated here to catch messages that were deferred.
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()

        if any(key == event_key for key, ts in self.processed_keys):
            return
            
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        
        if not rule: return

        # Apply content-type filters (photos, videos, etc.).
        if not self._is_message_allowed_by_filters(message_object, rule):
            return

        # Apply text length filters.
        is_text_based = not message.media or isinstance(message.media, (TLRPC.TL_messageMediaEmpty, TLRPC.TL_messageMediaWebPage))
        if is_text_based:
             if not (self.min_msg_length <= len(message.message or "") <= self.max_msg_length):
                return
        
        # Mark as processed and send.
        self.processed_keys.append((event_key, time.time()))
        self._send_forwarded_message(message_object, rule)

    def _build_reply_quote(self, message_object):
        """Builds a visual quote block for a replied-to message."""
        replied_message_obj = message_object.replyMessageObject
        if not replied_message_obj or not replied_message_obj.messageOwner:
            return None, None
        
        replied_message = replied_message_obj.messageOwner
        author_id = self._get_id_from_peer(replied_message.from_id)
        author_entity = self._get_chat_entity(author_id)
        author_name = self._get_entity_tag(author_entity)

        # Check if the replied-to message was itself a forward.
        original_fwd_tag, _ = self._get_original_author_details(replied_message.fwd_from)

        quote_snippet = ""
        if replied_message_obj.messageText:
            quote_snippet = str(replied_message_obj.messageText)
            if len(quote_snippet) > 40:
                quote_snippet = quote_snippet[:40] + "..."
        elif replied_message_obj.isPhoto():
            quote_snippet = "Photo"
        elif replied_message_obj.isVideo():
            quote_snippet = "Video"
        elif replied_message_obj.isVoice():
            quote_snippet = "Voice Message"
        elif replied_message_obj.isSticker():
            quote_snippet = "Sticker"
        else:
            quote_snippet = "Media"
        
        # Build the initial reply line.
        reply_line = f"Replying to {author_name}"
        
        # Append the original forward source if it exists.
        if original_fwd_tag:
            reply_line += f" (fwd from {original_fwd_tag})"
            
        quote_text = f"{reply_line}\n> {quote_snippet}"
        
        # Build rich text entities for the quote block.
        entities = ArrayList()
        italic_entity = TLRPC.TL_messageEntityItalic()
        italic_entity.offset = 0
        italic_entity.length = len(reply_line) # Use the length of the potentially extended line.
        entities.add(italic_entity)

        quote_entity = TLRPC.TL_messageEntityBlockquote()
        quote_entity.offset = quote_text.find('>')
        quote_entity.length = len(quote_snippet) + 2
        entities.add(quote_entity)

        return quote_text, entities

    def _send_album(self, message_objects, rule):
        """Constructs and sends an album, filtering each item and attaching a header/quote to the first."""
        if not message_objects: return
    
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})
    
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
                        if header_entities: prefix_entities.addAll(header_entities)
            
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
                                log(f"[{self.id}] Refreshed incomplete album part {original_message.id} from cache.")
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
        """Constructs and sends a single message."""
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

            # Build the prefix (header and/or quote) for the message.
            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(message, source_entity, author_entity)
                    if header_text:
                        prefix_text += header_text
                        if header_entities: prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(message_object)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        # Adjust offsets of quote entities to fit after the header text.
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            message_text = f"{prefix_text}\n\n{original_text}".strip()
            entities = self._prepare_final_entities(prefix_text, prefix_entities, original_entities)

            # Construct the appropriate API request based on content.
            req = None
            if input_media: # Media message
                req = TLRPC.TL_messages_sendMedia()
                req.media = input_media
                req.message = message_text
            elif message_text.strip(): # Text-only message
                req = TLRPC.TL_messages_sendMessage()
                req.message = message_text

            if req:
                req.peer = get_messages_controller().getInputPeer(to_peer_id)
                req.random_id = random.getrandbits(63)
                if entities and not entities.isEmpty():
                    req.entities = entities
                    req.flags |= 8 # Flag to indicate entities are present.
                
                send_request(req, RequestCallback(lambda r, e: None))

        except Exception:
            log(f"[{self.id}] ERROR in _send_forwarded_message: {traceback.format_exc()}")
            
    def _get_input_media(self, message_object):
        """Safely extracts forwardable media from a message object."""
        media = getattr(message_object.messageOwner, "media", None)
        if not media: return None
        try:
            if isinstance(media, TLRPC.TL_messageMediaPhoto) and hasattr(media, "photo"):
                photo = media.photo
                input_media = TLRPC.TL_inputMediaPhoto(); input_media.id = TLRPC.TL_inputPhoto()
                input_media.id.id, input_media.id.access_hash = photo.id, photo.access_hash
                # file_reference can sometimes be null, provide an empty bytearray as a fallback.
                input_media.id.file_reference = photo.file_reference or bytearray(0)
                return input_media

            if isinstance(media, TLRPC.TL_messageMediaDocument) and hasattr(media, "document"):
                doc = media.document
                input_media = TLRPC.TL_inputMediaDocument(); input_media.id = TLRPC.TL_inputDocument()
                input_media.id.id, input_media.id.access_hash = doc.id, doc.access_hash
                input_media.id.file_reference = doc.file_reference or bytearray(0)
                return input_media
        except Exception:
            log(f"[{self.id}] Failed to get input media: {traceback.format_exc()}")
        return None

    def create_settings(self) -> list:
        """Builds the plugin's settings page UI."""
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
                    text=f"From: {source_name}\nTo:   {dest_name} {style}",
                    icon="msg_edit",
                    on_click=lambda v, sid=source_id: self._show_rule_action_dialog(sid)
                ))
                settings_ui.append(Divider())
        settings_ui.extend([
            Divider(), Header(text="Support the Developer"),
            Text(text="TON", icon="msg_ton", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.TON_ADDRESS, "TON"))),
            Text(text="USDT (TRC20)", icon="msg_copy", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.USDT_ADDRESS, "USDT"))),
            Divider(),
            Text(text="Disclaimer & FAQ", icon="msg_help", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._show_faq_dialog())),
        ])
        
        return settings_ui

    def _show_faq_dialog(self):
        """Builds and displays the FAQ and Disclaimer in a themed, scrollable dialog."""
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
            
            # Manually parse custom markdown and convert to HTML for rich text display.
            def process_inline_markdown(text):
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text) # Links
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) # Bold
                text = re.sub(r'__(.*?)__', r'<u>\1</u>', text) # Underline
                text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text) # Strikethrough
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text) # Italics
                text = re.sub(r'`(.*?)`', r'<tt>\1</tt>', text) # Monospace
                return text

            # Fetch colors from the current Telegram theme for a native look and feel.
            accent_color_hex = f"#{Theme.getColor(Theme.key_dialogTextLink) & 0xFFFFFF:06x}"
            spoiler_color_hex = f"#{Theme.getColor(Theme.key_windowBackgroundGray) & 0xFFFFFF:06x}"

            html_lines = []
            for line in FAQ_TEXT.strip().split('\n'):
                stripped_line = line.strip()

                if not stripped_line:
                    html_lines.append('')
                    continue
                
                if stripped_line == '---':
                    html_lines.append(f"<p align='center'><font color='{accent_color_hex}'>•&nbsp;•&nbsp;•</font></p>")
                    continue
                
                # Handle list items, headers, and regular text, processing spoilers first.
                content_spoilers_processed = re.sub(r'\|\|(.*?)\|\|', rf'<font style="background-color:{spoiler_color_hex};color:{spoiler_color_hex};">&nbsp;\1&nbsp;</font>', stripped_line)
                if stripped_line.startswith('* '):
                    content_final = process_inline_markdown(content_spoilers_processed[2:])
                    html_lines.append(f"&nbsp;&nbsp;•&nbsp;&nbsp;{content_final}")
                elif re.match(r'^\*\*(.*)\*\*$', stripped_line):
                    content = stripped_line.replace('**', '').strip()
                    html_lines.append(f"<h4><font color='{accent_color_hex}'>{content}</font></h4>")
                else:
                    html_lines.append(process_inline_markdown(content_spoilers_processed))
            
            html_text = '<br>'.join(html_lines)
            
            # Clean up extra line breaks for better spacing.
            html_text = re.sub(r'(<br>){2,}', '<br>', html_text)
            html_text = html_text.replace('<br><p', '<p').replace('</p><br>', '</p>')
            html_text = html_text.replace('<br><h4', '<br><br><h4').strip()
            
            # Set the processed HTML text to the TextView.
            if hasattr(Html, 'FROM_HTML_MODE_LEGACY'):
                 faq_text_view.setText(Html.fromHtml(html_text, Html.FROM_HTML_MODE_LEGACY))
            else:
                 faq_text_view.setText(Html.fromHtml(html_text))

            faq_text_view.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            faq_text_view.setMovementMethod(LinkMovementMethod.getInstance()) # Makes links clickable
            faq_text_view.setLinkTextColor(Theme.getColor(Theme.key_dialogTextLink))
            faq_text_view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15)
            faq_text_view.setLineSpacing(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 2.0, activity.getResources().getDisplayMetrics()), 1.0)


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
            # JSON keys must be strings, so keys are converted back to integers on load.
            self.forwarding_rules = {int(k): v for k, v in json.loads(rules_str).items()}
        except Exception:
            self.forwarding_rules = {} # Fallback to empty rules on error.

    def _save_forwarding_rules(self):
        """Saves the current forwarding rules to persistent storage."""
        # Keys are converted to strings for JSON compatibility.
        self.set_setting(FORWARDING_RULES_KEY, json.dumps({str(k): v for k, v in self.forwarding_rules.items()}))
        self._load_forwarding_rules() # Reload to ensure consistency.

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
        if entity:
            return entity
        
        if input_id > 0:
            return controller.getUser(input_id)
            
        return None

    def _sanitize_chat_id_for_request(self, input_id: int) -> int:
        """Converts a user-provided ID into a server-compatible short ID for channel/supergroup lookups."""
        id_str = str(abs(input_id))
        # Supergroup/channel IDs often start with -100..., but the API needs the short version.
        if id_str.startswith("100") and len(id_str) > 9:
            try:
                return int(id_str[3:])
            except (ValueError, IndexError):
                pass
        return abs(input_id)

    def _get_chat_entity(self, dialog_id):
        """A robust way to get a chat entity from a dialog_id."""
        if not isinstance(dialog_id, int):
            try:
                dialog_id = int(dialog_id)
            except (ValueError, TypeError):
                return None
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
        if hasattr(entity, 'username') and entity.username: return f"@{entity.username}"
        return self._get_entity_name(entity)

    def _get_chat_name(self, chat_id):
        """A convenience function to get a chat name directly from its ID."""
        return self._get_entity_name(self._get_chat_entity(int(chat_id)))

    def _get_original_author_details(self, fwd_header):
        """Helper to extract original author details from a fwd_header."""
        if not fwd_header:
            return None, None
        original_author_tag = None
        original_author_entity = None
        original_author_id = self._get_id_from_peer(getattr(fwd_header, 'from_id', None))
        if original_author_id:
            original_author_entity = self._get_chat_entity(original_author_id)
            if original_author_entity:
                original_author_tag = self._get_entity_tag(original_author_entity)
        elif hasattr(fwd_header, 'from_name') and fwd_header.from_name:
            original_author_tag = fwd_header.from_name
        return original_author_tag, original_author_entity

    def _prepare_final_entities(self, prefix_text, prefix_entities, original_entities):
        """Combines prefix entities (headers/quotes) and original message entities, adjusting offsets."""
        final_entities = ArrayList()
        if prefix_entities: final_entities.addAll(prefix_entities)
        
        if original_entities and not original_entities.isEmpty():
            # Shift the offset of all original entities to appear after the prefix.
            offset_shift = len(prefix_text) + 2 if prefix_text else 0
            for i in range(original_entities.size()):
                old = original_entities.get(i)
                new = type(old)(); new.offset, new.length = old.offset + offset_shift, old.length
                # Copy relevant properties for different entity types.
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
        original_author_tag, _ = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {name}"
        if original_author_tag:
            text += f" (fwd_from {original_author_tag})"
        
        # Create a clickable link to the original message in the channel.
        link = TLRPC.TL_messageEntityTextUrl(); link.offset, link.length = text.find(name), len(name)
        msg_id = message.fwd_from.channel_post if message.fwd_from and message.fwd_from.channel_post else message.id
        link.url = f"https://t.me/{channel.username}/{msg_id}" if channel.username else f"https://t.me/c/{channel.id}/{msg_id}"
        entities.add(link)
        return text, entities

    def _build_group_header(self, message, group, author):
        """Builds the header for forwards from a group, with mentions and links."""
        group_name = self._get_entity_name(group)
        author_tag = self._get_entity_tag(author)
        entities = ArrayList()
        original_author_tag, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {group_name} (by {author_tag})"
        if original_author_tag:
            text += f" fwd_from {original_author_tag}"

        # Link to the message if it's a supergroup.
        if isinstance(group, TLRPC.TL_channel):
             msg_id = message.id
             group_link = f"https://t.me/{group.username}/{msg_id}" if group.username else f"https://t.me/c/{group.id}/{msg_id}"
             link_entity = TLRPC.TL_messageEntityTextUrl(); link_entity.offset, link_entity.length, link_entity.url = text.find(group_name), len(group_name), group_link
             entities.add(link_entity)
        else: # Regular groups don't have message links, so just bold the name.
            bold = TLRPC.TL_messageEntityBold(); bold.offset, bold.length = text.find(group_name), len(group_name)
            entities.add(bold)
        
        # Create a clickable mention for the author if they don't have a public @username.
        if author and isinstance(author, TLRPC.TL_user) and not author.username:
            mention = TLRPC.TL_messageEntityMentionName(); mention.offset, mention.length = text.find(author_tag), len(author_tag)
            mention.user_id = author.id
            if mention.user_id: entities.add(mention)
        
        # Also create a mention for the original author if applicable.
        if original_author_entity and isinstance(original_author_entity, TLRPC.TL_user) and not original_author_entity.username:
            mention = TLRPC.TL_messageEntityMentionName()
            try:
                search_start = text.index(author_tag) + len(author_tag)
                mention.offset = text.index(original_author_tag, search_start)
                mention.length = len(original_author_tag)
                mention.user_id = original_author_entity.id
                if mention.user_id: entities.add(mention)
            except ValueError:
                pass # Should not happen if tag is present.
        return text, entities

    def _build_private_header(self, message, sender, receiver):
        """Builds the header for private chats, mentioning users where possible."""
        sender_tag = self._get_entity_tag(sender)
        receiver_tag = self._get_entity_tag(receiver)
        entities = ArrayList()
        original_author_tag, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {sender_tag} to {receiver_tag}"
        if original_author_tag:
            text += f" (original fwd_from {original_author_tag})"
        
        # Create clickable mentions for any participant who doesn't have a public @username.
        for entity, tag in [(sender, sender_tag), (receiver, receiver_tag), (original_author_entity, original_author_tag)]:
            if entity and isinstance(entity, TLRPC.TL_user) and not entity.username:
                try:
                    mention = TLRPC.TL_messageEntityMentionName()
                    if tag is None: continue
                    mention.offset = text.index(tag)
                    mention.length = len(tag)
                    mention.user_id = entity.id
                    if mention.user_id: entities.add(mention)
                except ValueError:
                    continue
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
        if not current_chat_id:
            return
        current_chat_id = int(current_chat_id)

        # If a rule exists, show the management dialog. Otherwise, show the creation dialog.
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

            # Programmatically create the entire layout for the dialog.
            main_layout = LinearLayout(activity)
            main_layout.setOrientation(LinearLayout.VERTICAL)
            
            input_field = EditText(activity)
            input_field_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            input_field_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            input_field.setHint("Link, @username, or ID")
            input_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            input_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            input_field.setLayoutParams(input_field_params)
            main_layout.addView(input_field)

            # Define checkbox colors based on the current theme.
            checkbox_tint_list = ColorStateList([[-16842912], [16842912]], [Theme.getColor(Theme.key_checkbox), Theme.getColor(Theme.key_checkboxCheck)])
            
            # Create all checkboxes for rule options.
            drop_author_checkbox = CheckBox(activity)
            drop_author_checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            drop_author_checkbox_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            drop_author_checkbox.setText("Remove Original Author (Copy)")
            drop_author_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            drop_author_checkbox.setButtonTintList(checkbox_tint_list)
            drop_author_checkbox.setLayoutParams(drop_author_checkbox_params)
            main_layout.addView(drop_author_checkbox)

            quote_replies_checkbox = CheckBox(activity)
            quote_replies_checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            quote_replies_checkbox_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            quote_replies_checkbox.setText("Quote Replies")
            quote_replies_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            quote_replies_checkbox.setButtonTintList(checkbox_tint_list)
            quote_replies_checkbox.setLayoutParams(quote_replies_checkbox_params)
            main_layout.addView(quote_replies_checkbox)
            
            forward_own_checkbox = CheckBox(activity)
            forward_own_checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            forward_own_checkbox_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            forward_own_checkbox.setText("Forward My Own Messages")
            forward_own_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_own_checkbox.setButtonTintList(checkbox_tint_list)
            forward_own_checkbox.setLayoutParams(forward_own_checkbox_params)
            main_layout.addView(forward_own_checkbox)
            
            # Add a visual divider.
            divider_view = View(activity)
            divider_view.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_height_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 1, activity.getResources().getDisplayMetrics()))
            divider_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, divider_height_px)
            divider_params.setMargins(margin_px, margin_px, margin_px, margin_px // 2)
            divider_view.setLayoutParams(divider_params)
            main_layout.addView(divider_view)
            
            header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            header_params.setMargins(margin_px, 0, margin_px, 0)
            filter_header = TextView(activity)
            filter_header.setText("Content to forward:")
            filter_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            filter_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            filter_header.setLayoutParams(header_params)
            main_layout.addView(filter_header)
            
            # Create checkboxes for all content filters.
            filter_checkboxes = {}
            cb_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            cb_params.setMargins(margin_px, 0, margin_px, 0)
            for key, label in FILTER_TYPES.items():
                cb = CheckBox(activity)
                cb.setText(label)
                cb.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                cb.setButtonTintList(checkbox_tint_list)
                cb.setLayoutParams(cb_params)
                main_layout.addView(cb)
                filter_checkboxes[key] = cb

            # If modifying an existing rule, populate the dialog with the current settings.
            if existing_rule:
                destination_id = existing_rule.get("destination", 0)
                dest_entity = self._get_chat_entity(destination_id)
                identifier_to_set = str(destination_id)
                if dest_entity and hasattr(dest_entity, 'username') and dest_entity.username:
                    identifier_to_set = f"@{dest_entity.username}"
                input_field.setText(identifier_to_set)
                
                drop_author_checkbox.setChecked(existing_rule.get("drop_author", False))
                quote_replies_checkbox.setChecked(existing_rule.get("quote_replies", True))
                forward_own_checkbox.setChecked(existing_rule.get("forward_own", True))
                
                current_filters = existing_rule.get("filters", {})
                for key, cb in filter_checkboxes.items():
                    cb.setChecked(current_filters.get(key, True))
            else: # Otherwise, set default values for a new rule.
                drop_author_checkbox.setChecked(False) 
                quote_replies_checkbox.setChecked(True)
                forward_own_checkbox.setChecked(True)
                for cb in filter_checkboxes.values():
                    cb.setChecked(True)

            scroller = ScrollView(activity)
            scroller.addView(main_layout)
            builder.set_view(scroller)

            # Define the callback for the "Set" button.
            def on_set_click(b, w):
                filter_settings = {key: cb.isChecked() for key, cb in filter_checkboxes.items()}
                self._process_destination_input(
                    source_id, source_name, input_field.getText().toString(),
                    drop_author_checkbox.isChecked(), 
                    quote_replies_checkbox.isChecked(),
                    forward_own_checkbox.isChecked(),
                    filter_settings
                )

            builder.set_positive_button("Set", on_set_click)
            builder.set_negative_button("Cancel", lambda b, w: b.dismiss())
            run_on_ui_thread(lambda: builder.show())
        except Exception:
            log(f"[{self.id}] ERROR showing rule setup dialog: {traceback.format_exc()}")

    def _process_destination_input(self, source_id, source_name, user_input, drop_author, quote_replies, forward_own, filter_settings):
        """Handles all destination types with a multi-step resolution logic."""
        cleaned_input = (user_input or "").strip()
        if not cleaned_input: return

        # Strategy 1: Resolve as a private invite link.
        if "/joinchat/" in cleaned_input or "/+" in cleaned_input:
            self._resolve_as_invite_link(cleaned_input, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings)
            return
            
        try:
            # Strategy 2: Resolve as a numeric ID.
            input_as_int = int(cleaned_input)
            cached_entity = self._get_chat_entity_from_input_id(input_as_int)
            if cached_entity: # If ID is in local cache, use it directly.
                self._finalize_rule(source_id, source_name, self._get_id_for_storage(cached_entity), self._get_entity_name(cached_entity), drop_author, quote_replies, forward_own, filter_settings)
                return
            # If not in cache, perform a network lookup.
            self._resolve_by_id_shotgun(input_as_int, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings)
        except ValueError:
            # Strategy 3: If not a number, resolve as a public username.
            self._resolve_as_username(cleaned_input, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings)
            
    def _resolve_as_invite_link(self, cleaned_input, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings):
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
                    self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), drop_author, quote_replies, forward_own, filter_settings)

            send_request(req, RequestCallback(on_check_invite))
        except Exception as e:
            log(f"[{self.id}] Failed to process invite link: {e}")

    def _resolve_by_id_shotgun(self, input_as_int, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings):
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
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), drop_author, quote_replies, forward_own, filter_settings)
            else:
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}")

        # The "shotgun" approach: try multiple variations of the ID (positive, negative, sanitized)
        # because the correct format required by the API can be ambiguous.
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

    def _resolve_as_username(self, username, source_id, source_name, drop_author, quote_replies, forward_own, filter_settings):
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
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), drop_author, quote_replies, forward_own, filter_settings)
            else:
                BulletinHelper.show_error(f"Could not resolve '{username}'.")
        try:
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = username.replace("@", "").split("/")[-1] # Sanitize input
            send_request(req, RequestCallback(on_resolve_complete))
        except Exception:
            log(f"[{self.id}] ERROR resolving username: {traceback.format_exc()}")
    
    def _finalize_rule(self, source_id, source_name, destination_id, dest_name, drop_author, quote_replies, forward_own, filter_settings):
        """Saves a fully resolved rule to storage and shows a success message."""
        if destination_id == 0:
            log(f"[{self.id}] Finalize rule called with invalid destination_id=0. Aborting.")
            BulletinHelper.show_error("Failed to save rule: Invalid destination chat resolved.")
            return
        
        rule_data = {
            "destination": destination_id,
            "enabled": True,
            "drop_author": drop_author,
            "quote_replies": quote_replies,
            "forward_own": forward_own,
            "filters": filter_settings
        }
        self.forwarding_rules[source_id] = rule_data
        self._save_forwarding_rules()
        run_on_ui_thread(lambda: self._show_success_dialog(source_name, dest_name))

    def _show_success_dialog(self, source_name, dest_name):
        """Shows a success message after a rule is set."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Success!"); builder.set_message(f"Rule for '{source_name}' set to '{dest_name}'.")
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
            builder.set_positive_button("Delete", lambda b, w: self._execute_delete(source_id)); builder.set_negative_button("Cancel", None)
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

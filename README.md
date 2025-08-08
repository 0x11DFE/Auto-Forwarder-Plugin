# Auto Forwarder Plugin

[![Version](https://img.shields.io/badge/version-1.9.0-blue.svg)](https://github.com/0x11DFE/Auto-Forwarder-Plugin/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Telegram](https://img.shields.io/badge/author-%40T3SL4-blue.svg)](https://t.me/T3SL4)

An advanced plugin for **exteraGram** that gives you total control over message forwarding. Automatically copy or forward messages from any chat to another with powerful filters, an integrated auto-updater, and a robust engine for reliable, ordered delivery.

> [!WARNING]
> ### 🔐 Disclaimer – Read Before Using
> > This plugin automates actions on your personal Telegram account, a practice often called "self-botting." It is provided for educational, testing, and personal automation purposes only. The author does not encourage any activity that violates Telegram’s Terms of Service.
> > - **Misuse can lead to account limitations or bans.** You are solely responsible for how you use this tool.
> > - By using this plugin, you agree to use it responsibly, ethically, and **entirely at your own risk.** The author assumes no liability for any consequences arising from its use.

---

### 📚 Table of Contents
* [Features](#-features)
* [Installation](#%EF%B8%8F-installation)
* [How to Use](#-how-to-use)
* [Configuration](#%EF%B8%8F-configuration)
* [Contributing](#-contributing)
* [Support the Developer](#%EF%B8%8F-support-the-developer)
* [License](#-license)

---

## 📸 Preview

![Plugin Preview](https://github.com/0x11DFE/Auto-Forwarder-Plugin/raw/refs/heads/main/auto_forwarder_preview.gif)


## ✨ Features

* **🚀 Reliable, Ordered Forwarding:**
    * **Sequential Processing Engine:** A completely new architecture that processes messages one-by-one in a dedicated queue. This resolves race conditions and **guarantees that messages are forwarded in the exact order they are received.**
    * **Configurable Speed vs. Order:** The new `Sequential Delay (Seconds)` setting gives you direct control over the trade-off. A small delay ensures order for large batches of files, while setting it to `0` restores high-speed parallel processing (which may result in messages being forwarded out of order).

* **Effortless Destination & Topic Setup:**
    * **Set by Replying:** The easiest way to set up a rule. Simply tap "Set by Replying" in the rule dialog, then go to your destination chat and reply to *any* message with the word `set`. The plugin handles the rest.
    * **Full Topic Support:** Automatically forward messages directly into a specific topic in a group or a comment thread in a channel. The "Set by Replying" feature makes this seamless.

* **Seamless Auto-Updater:**
    * Get notified directly in the app when a new version is available on GitHub Releases.
    * View the official changelog in a pop-up dialog before updating.
    * Update with a single click—no manual downloads or installs required.

* **Two Powerful Forwarding Modes:**
    * **Copy Mode:** Sends a brand new message, making it look like you sent it yourself. This mode enables perfect formatting preservation and automatically recreated reply quotes.
    * **Header Mode (Simulated Forward):** Copies the message and prepends a custom, clickable "Forwarded from..." header, linking to the original author and chat.

* **Advanced Filtering Engine:**
    * **Keyword & Regex:** Forward messages, media captions, or **documents with filenames** that contain specific keywords or match a regular expression.
    * **Granular Content Control:** The "Text" filter is now split into "Text Messages" and "Media Captions," allowing you to forward media while stripping its caption, and vice-versa.
    * **Author Whitelisting:** Filter messages based on the author type (Users, Bots, Outgoing), or provide a specific, comma-separated list of User IDs or `@usernames` to exclusively forward messages *only* from them.

* **Intelligent & Reliable Processing:**
    * **Ordered Album Handling:** Automatically waits to collect all photos/videos in a gallery before sending them together as a single, correctly ordered album.
    * **Duplicate Notification Prevention:** A thread-safe deduplication system prevents client-side notification glitches from causing the same message to be forwarded multiple times.
    * **Anti-Spam Firewall:** A built-in rate-limiter prevents a single user from flooding your destination chat with rapid messages.


## 🛠️ Installation

1.  Go to the [**Releases**](https://github.com/0x11DFE/Auto-Forwarder-Plugin/releases) page and download the latest `.py` file.
2.  Using your device's file manager, **rename the file extension** from `.py` to `.plugin`. (Your file manager may warn you about changing the extension; accept the change.)
3.  Open Telegram and send the `.plugin` file to yourself (e.g., in your "Saved Messages").
4.  Tap on the file you just sent within the Telegram app.
5.  A confirmation dialog will appear. Tap **INSTALL PLUGIN** to finish.

> After the first installation, the plugin can update itself using the built-in updater.

## 📖 How to Use

This plugin is configured entirely through the Telegram user interface.

### Creating a Rule (The Easy Way)
1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (**⋮**) in the top-right corner and select **Auto Forward...**.
3.  In the rule setup dialog, tap the **"Set by Replying"** button.
4.  A prompt will appear. Click **Proceed**.
5.  Navigate to your desired destination chat. This can be a user, group, channel, or even a specific **topic/comment thread**.
6.  **Reply** to any message in that destination with the exact word: `set`
7.  The plugin will instantly configure the rule and delete your `set` message. You're done!

### Creating a Rule (Manual Method)
1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (**⋮**) in the top-right corner and select **Auto Forward...**.
3.  A dialog will appear. Manually enter the destination chat's ID, @username, or private `t.me/joinchat/...` link.
4.  Configure the other options, such as content filters, keyword matching, and specific author whitelists.
5.  Tap **Set** to save the rule.

### Editing or Deleting a Rule
1.  Go into a chat that already has an active forwarding rule.
2.  Open the **Auto Forward...** menu item again.
3.  A management dialog will appear, allowing you to **Modify** or **Delete** the rule for that chat.

## ⚙️ Configuration

All global settings and a list of all active rules can be found by going to:
`Settings > exteraGram Settings > Plugins > Auto Forwarder`

Key settings include:
- **Album Buffering Timeout (ms):** How long to wait to collect all media in an album.
- **Sequential Delay (Seconds):** The pause between each message to guarantee order. Set to `0` to restore high-speed parallel mode (order not guaranteed).
- **Deduplication Window (Seconds):** Time window to ignore duplicate notifications from the client.

At the bottom of this page, you will also find the **"Check for Updates"** button.


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/0x11DFE/Auto-Forwarder-Plugin/issues).

## ❤️ Support the Developer

If you find this plugin useful, please consider supporting its development. Thank you!

* **TON:** `UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm`
* **USDT (TRC20):** `TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo`


## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) for the full license text.

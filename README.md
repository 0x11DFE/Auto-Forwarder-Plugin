# Message Forwarder Plugin

[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/0x11DFE/Auto-Forwarder-Plugin/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Telegram](https://img.shields.io/badge/author-%40T3SL4-blue.svg)](https://t.me/T3SL4)

An advanced plugin for exteraGram clients to automatically forward or copy messages from any chat to another, with powerful filters and customization.

> **🔐 ⚠️ DISCLAIMER – READ BEFORE USING ⚠️**
> This plugin automates actions on your personal Telegram account, a practice often called "self-botting." This is provided for educational, testing, and personal automation purposes only.
>
> The author does not encourage or support any form of abuse or activity that violates [Telegram’s Terms of Service](https://telegram.org/tos).
> - Misuse of this plugin to automate actions in a way that mimics bot activity can result in account limitations or permanent bans. You are solely responsible for how you use this tool.
> - By using this plugin, you agree to use it responsibly, ethically, and entirely at your own risk. The author assumes no liability for any actions taken with or consequences arising from its use.

---

## 📸 Preview

![Plugin Preview](https://github.com/0x11DFE/Auto-Forwarder-Plugin/raw/refs/heads/main/auto_forwarder_preview.gif)


## ✨ Features

* **Two Forwarding Modes:**
    * **Copy Mode:** Sends a brand new message, making it look like you sent it yourself. Perfectly preserves all text formatting.
    * **Forward Mode:** Performs a standard Telegram forward with the "Forwarded from" header.
* **Forward from Anywhere:** Create rules for any chat, including private messages, groups, and channels.
* **Advanced Content Filtering:** For each rule, you can select exactly which types of content to forward (Text, Photos, Videos, Documents, Stickers, etc.).
* **Full Formatting Preservation:** In Copy Mode, all rich text formatting is kept intact, including **bold**, *italic*, `monospace`, ~~strikethrough~~, ||spoilers||, and [hyperlinks](https://telegram.org).
* **Intelligent Buffering:**
    * **Album Handling:** Automatically waits to collect all photos/videos in an album before sending them together.
    * **Media Deferral:** Includes a safety net for large or slow-to-download media, ensuring files are forwarded reliably.
* **Anti-Spam Firewall:** A built-in rate-limiter prevents a single user from flooding your destination chat.
* **Highly Configurable:**
    * Set global settings for message length, timeouts, and anti-spam delays.
    * Configure each rule individually with its own filters and forwarding mode.


## ⚙️ Installation

1.  Go to the [**Releases**](https://github.com/0x11DFE/Auto-Forwarder-Plugin/releases) page and download the latest `.py` file.
2.  Using your device's file manager, **rename the file extension** from `.py` to `.plugin`.
3.  Send the `.plugin` file to yourself in Telegram (e.g., in your "Saved Messages").
4.  Tap on the file you just sent. The client will show a confirmation dialog.
5.  Tap **INSTALL PLUGIN** to finish.

## 🚀 How to Use

This plugin is configured entirely through the Telegram user interface.

### Creating a Rule

1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (⋮) in the top-right corner.
3.  Select **Auto Forward...** from the menu.
4.  A dialog will appear. Enter the destination chat's ID, @username, or private invite link.
5.  Configure the options (like Copy/Forward mode and content filters).
6.  Tap "Set" to save the rule.

### Editing or Deleting a Rule

1.  Go into a chat that already has an active forwarding rule.
2.  Open the **Auto Forward...** menu item again.
3.  A management dialog will appear, allowing you to **Modify** or **Delete** the rule for that chat.

You can also see a list of all your active rules from the main plugin settings page.

## 🔧 Configuration

All global settings (timeouts, anti-spam delay, etc.) and a list of all rules can be found by going to:
`Settings > exteraGram Settings > Plugins > Auto Forwarder`


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/0x11DFE0x11DFE/Auto-Forwarder-Plugin/issues).

## ❤️ Support the Developer

If you find this plugin useful, please consider supporting its development. Thank you!

* **TON:** `UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm`
* **USDT (TRC20):** `TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo`


## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) file for the full license text.

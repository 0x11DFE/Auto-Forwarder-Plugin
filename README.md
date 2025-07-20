# Auto Forwarder Plugin

[![Version](https://img.shields.io/badge/version-1.6.5-blue.svg)](https://github.com/0x11DFE/Auto-Forwarder-Plugin/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Telegram](https://img.shields.io/badge/author-%40T3SL4-blue.svg)](https://t.me/T3SL4)

An advanced plugin for **exteraGram** that gives you total control over message forwarding. Automatically copy or forward messages from any chat to another with powerful filters, an integrated auto-updater, and perfect format preservation.

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

* **Seamless Auto-Updater:**
    * Get notified directly in the app when a new version is available on GitHub Releases.
    * View the official changelog in a pop-up dialog before updating.
    * Update with a single click—no manual downloads or installs required.
    * Includes both automatic background checks and a manual check button.

* **Two Powerful Forwarding Modes:**
    * **Copy Mode:** Sends a brand new message, making it look like you sent it yourself. This mode enables:
        * **Perfect Formatting:** Preserves **bold**, *italic*, `monospace`, ~~strikethrough~~, ||spoilers||, and [hyperlinks](https://telegram.org).
        * **Reply Quoting:** Automatically recreates the replied-to message as a visual quote block.
    * **Header Mode (Simulated Forward):** Copies the message and prepends a custom, clickable "Forwarded from..." header, linking to the original author and chat.

* **Keyword & Regex Filtering:**
    * Create rules that only forward messages or media captions containing specific keywords or matching a regular expression.
    * Features a case-insensitive, fallback search for invalid regex patterns.

* **Advanced Content Filtering:**
    * For each rule, precisely select which types of content to forward (Text, Photos, Videos, Documents, Stickers, etc.).
    * Filter messages based on the author (Users, Bots, or your own Outgoing messages).

* **Intelligent Buffering & Anti-Spam:**
    * **Album Handling:** Automatically waits to collect all photos/videos in a gallery before sending them together as a single album.
    * **Media Deferral:** Includes a safety net for large or slow-to-download media, retrying to ensure files are forwarded reliably.
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

### Creating a Rule
1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (**⋮**) in the top-right corner.
3.  Select **Auto Forward...** from the menu.
4.  A dialog will appear. Enter the destination chat's ID, @username, or private `t.me/joinchat/...` link.
5.  Configure the options (like Copy/Header mode, content filters, and keyword filters).
6.  Tap **Set** to save the rule.

### Editing or Deleting a Rule
1.  Go into a chat that already has an active forwarding rule.
2.  Open the **Auto Forward...** menu item again.
3.  A management dialog will appear, allowing you to **Modify** or **Delete** the rule for that chat.

## ⚙️ Configuration

All global settings and a list of all active rules can be found by going to:
`Settings > exteraGram Settings > Plugins > Auto Forwarder`

At the bottom of this page, you will also find the **"Check for Updates"** button.


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/0x11DFE/Auto-Forwarder-Plugin/issues).

## ❤️ Support the Developer

If you find this plugin useful, please consider supporting its development. Thank you!

* **TON:** ``UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm``
* **USDT (TRC20):** ``TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo``


## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) file for the full license text.

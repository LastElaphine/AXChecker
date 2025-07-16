
# Anime Expo Guest Checker

This script periodically checks the official Anime Expo guest page for new additions and sends a push notification with the guest's photo to your phone using the free ntfy.sh service.

## Features

- Monitors the AX guest page without requiring a full browser (lightweight and fast).
- Extracts guest name, a link to their details page, and their photo.
- Sends instant push notifications to your phone via ntfy.sh.
- Includes the guest's photo directly in the notification.
- Designed to be run as a robust background service on a Linux server.

## Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/ax-checker.git
    cd ax-checker
    ```

2.  **Create a Python Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Push Notifications**
    - Download the **ntfy** app on your [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) or [iOS](https://apps.apple.com/us/app/ntfy/id1625396347) device.
    - Subscribe to a unique, private topic name (e.g., `ax-alerts-super-secret-123`).

## Configuration

This script is configured using an environment variable to keep your notification topic secret.

Set the `NTFY_TOPIC` environment variable to the topic name you subscribed to:

```bash
export NTFY_TOPIC="your-secret-topic-name"
```

The script will read this variable automatically. Do not write your topic name in the script itself.

## Deployment (using systemd)

The most reliable way to run this is as a `systemd` service on a Linux server.

1.  Copy the included `ax-checker.service.template` file to `/etc/systemd/system/ax-checker.service`.
2.  Edit the file, making sure to set your `User`, `Group`, `WorkingDirectory`, and the `NTFY_TOPIC` environment variable.
3.  Run the following commands:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable ax-checker.service
    sudo systemctl start ax-checker.service
    ```

## Checking Logs

To check if the service is running correctly and see its output, use `journalctl`:

```bash
sudo journalctl -u ax-checker.service -f
```
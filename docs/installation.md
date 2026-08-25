# WFD v1.0 Installation

## HACS

1. Open HACS in Home Assistant.
2. Open **Integrations** and search for **What's For Dinner**.
3. Install the integration.
4. Restart Home Assistant.
5. Go to **Settings -> Devices & services -> Add integration**.
6. Select **What's For Dinner** and choose the default meals-per-round and deadline.

The integration stores its data in Home Assistant's `.storage/wfd.storage` file.

## First setup

Create a Home Assistant Person for each household member and link each person's Home Assistant user account. WFD discovers active Person entities automatically.

The Home Assistant users who should manage WFD must be Home Assistant administrators. Non-admin users can only access voting while a round is open, and can vote only as themselves.

## Upgrade

1. Back up Home Assistant.
2. Update WFD through HACS.
3. Restart Home Assistant.
4. Confirm the WFD panel loads and existing meals, voters, rounds, and results remain available.

## Backup and recovery

Stop Home Assistant before copying `.storage/wfd.storage`.

To restore:

1. Stop Home Assistant.
2. Replace `.storage/wfd.storage` with the backup.
3. Start Home Assistant.
4. Confirm the WFD panel and completed results.

Never edit the storage file while Home Assistant is running.

# WFD v1.0 Installation

## HACS

1. Open HACS in Home Assistant.
2. Open **Integrations** and search for **What's For Dinner**.
3. Install WFD.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**.
6. Select **What's For Dinner** and complete the setup.

## First setup

Create a Home Assistant Person for each household member and, where applicable, link that Person to the household member's Home Assistant user account.

WFD uses Home Assistant Persons as the household identity source. WFD administrators must use Home Assistant administrator accounts. Non-admin users can vote while a round is open and can vote only as themselves.

During setup you choose the default number of meals to select per round and the default voting deadline. These defaults can be overridden when an administrator starts a round.

## Upgrade

1. Back up Home Assistant.
2. Update WFD through HACS.
3. Restart Home Assistant.
4. Open the WFD panel and confirm existing meals, voters, rounds and results are still present.

## Backup and recovery

WFD stores its data in Home Assistant's `.storage/wfd.storage` file.

For backup or recovery:

1. Stop Home Assistant.
2. Copy the existing `wfd.storage` file to a safe location, or replace it with a known-good backup.
3. Start Home Assistant.
4. Confirm the WFD panel and completed results load correctly.

Never edit the storage file while Home Assistant is running.

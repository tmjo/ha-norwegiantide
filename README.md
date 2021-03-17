# Norwegian Tide

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) ![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

This is a Home Assistant custom integration for Norwegian Tide which is interfacing an open API by the [Norwegian Mapping Authority (Kartverket)](https://kartverket.no/en/), more precisely [sehavniva.no](http://www.sehavniva.no/) which provides information about water levels and tidal predicitions and forecasts. **All data is ©Kartverket**.

Unfortunately the service only provides data for geographical positions in Norway - this is a limitation in the API and not in this integration.


## Installation
There are different methods of installing the custom component. HACS is by far the simplest way for unexperienced users and is recomended.

### HACS installation
The installation is currently not included in HACS as a default repo, but can be installed through HACS *by adding this repo as a custom repository*.

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant environment.
2. Go to **HACS**, select **Integrations**.
3. Click on the three dots in the upper right corner and select **Custom repositories**
4. Copy/paste the **URL for this repo** `https://github.com/tmjo/ha-norwegiantide` into the URL-field, select **Integration as category** and then click **Add**.
5. You should now find the **Norwegian Tide** integration by searching for it in HACS, proceed to install it.
6. Restart Home Assistant (a warning should be shown in log saying you're using a custom integration).
7. Continue to the Configuration-section.


### Manual
1. Navigate to you home assistant configuration folder.
2. Create a `custom_components` folder of it does not already exist, then navigate into it.
3. Download the folder `norwegian-tide` from this repo and add it into your custom_components folder.
4. Restart Home Assistant (a warning should be shown in log saying you're using a custom integration).
5. Continue to the Configuration-section.


### Git installation
1. Make sure you have git installed on your machine.
2. Navigate to you home assistant configuration folder.
3. Create a `custom_components` folder of it does not already exist, then navigate into it.
4. Execute the following command: `git clone https://github.com/tmjo/ha-norwegiantide ha-norwegiantide`
5. Run `bash links.sh`
6. Restart Home Assistant (a warning should be shown in log saying you're using a custom integration).
7. Continue to the Configuration-section.

## Configuration
Configuration is done through UI/Lovelace. In Home Assistant, click on Configuration > Integrations where you add it with the + icon.

## Usage


## Issues and development
Please report issues on github. If you would like to contribute to development, please do so through PRs.
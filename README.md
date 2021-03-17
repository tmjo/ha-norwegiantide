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

You will be asked to give your location a name and to provide latitude and longitude as geographical position for the location you want to track. Finally select which sensors you would like the integration to add. More detailed description of this will be added, but in short there is one main sensor which contains most info and for most people probably will be sufficient. You do not need to add the other sensor unless you want, but several detailed sensors are available if you decide to add them.

It is also possible to enable more than one location by adding the integration several times.

## Usage
I strongly suggest to take a look at the [Apexchart-card] (https://github.com/RomRider/apexcharts-card) by Romrider - it is an excellent graph card for lovelace which also enables the possibility to show future values. This is necessary to display prediction- and forecast values.

More detailed description will follow, but worth mentioning:
 - Prediction: A calculated prediction for the location
 - Forecast: Includes the weather effect on top of the prediction
 - Observation: The observed value on the closest station to your location


## Issues and development
Please report issues on github. If you would like to contribute to development, please do so through PRs.
# Norwegian Tide

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) ![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

{% if pending_update %}
## New version is available
{% endif %}
{% if prerelease %}
### NB!: This is a Beta version!
{% endif %}

This is a Home Assistant custom integration for Norwegian Tide which is interfacing an open API by the [Norwegian Mapping Authority (Kartverket)](https://kartverket.no/en/), more precisely [sehavniva.no](http://www.sehavniva.no/) which provides information about water levels and tidal predicitions and forecasts. **All data is ©Kartverket**.

Unfortunately the service only provides data for geographical positions in Norway - this is a limitation in the API and not in this integration.


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

For further information, see [README](https://github.com/tmjo/ha-norwegiantide)
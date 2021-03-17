# Custom improvement of the offial HA integration for Denon HEOS

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) ![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)

{% if pending_update %}
## New version is available
{% endif %}
{% if prerelease %}
### NB!: This is a Beta version!
{% endif %}


The official integration for [Denon HEOS](https://www.home-assistant.io/integrations/heos/) in [Home Assistant](https://www.home-assistant.io/) unfortunately lacks the grouping feature. Work is ongoing to add such features to the official integration, but due to some architectual discussions and the time it takes to conclude those, this custom integration allows HEOS-users to start grouping already today. Once this is implemented in the official integration, this custom integration will probably cease to exist. Follow the progress on official work (by others) [here](https://github.com/home-assistant/architecture/issues/364) and [here](https://github.com/home-assistant/core/pull/32568).

The grouping feature is available as service calls **join** and **unjoin** but for the best user experience I recommend using the amazing [mini-media-card](https://github.com/kalkih/mini-media-player) which has the grouping feature working from UI/Lovelace.

**DISCLAIMER:** I am *not* the codeowner of the official HEOS integration and do not take credit for anything else but adding a grouping-hack while waiting for official support of the feature. Credits for the hard work belongs to [Andrew Sayre](https://github.com/andrewsayre) who is the author of both the [official integration](https://www.home-assistant.io/integrations/heos/) and the [PyHeos library](https://github.com/andrewsayre/pyheos).



## Configuration
Configuration is done through UI/Lovelace. In Home Assistant, click on Configuration > Integrations where you add it with the + icon.

## Usage
This custom integration should work the same way as the [official integration](https://www.home-assistant.io/integrations/heos/) but has added a grouping feature to enable you to group you speakers - just like you can do it in the HEOS app on you mobile or tablet.

Either use the service calls **join** and **unjoin**, and be sure to check out the amazing [mini-media-card](https://github.com/kalkih/mini-media-player) which has the grouping feature working from UI/Lovelace. With that card you can control grouping easily from your UI.

For further information, see [README](https://github.com/tmjo/heos_custom)
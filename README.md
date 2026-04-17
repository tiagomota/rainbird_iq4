<p align="center">
  <img src="https://raw.githubusercontent.com/tiagomota/ha-rainbird-iq4/refs/heads/main/custom_components/rainbird_iq4/brand/logo.png" alt="BMW Cardata logo" width="600" />
</p>

# RainBird IQ4 - Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for RainBird IQ4 irrigation controllers using the IQ4 cloud API.

The official Home Assistant Rain ird integration only supports the legacy local LNK WiFi module. If your controller has been updated to RainBird 2.0 firmware, the local API no longer works. This integration connects via the RainBird IQ4 cloud API instead.

## Features

- **Program switches** - Enable/disable irrigation programs (A, B, C)
- **Seasonal adjustment** - Adjust program watering percentage (0-300%)
- **Rain delay sensor** - View current rain delay in days
- **Connection status** - Monitor controller connectivity
- **Shutdown status** - Monitor controller shutdown state
- **Multi-controller support** - Add the integration once per controller

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots menu in the top right
3. Select "Custom repositories"
4. Add `https://github.com/tiagomota/ha-rainbird-iq4` with category "Integration"
5. Install "RainBird IQ4"
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/rainbird_iq4` directory to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "RainBird IQ4"
3. Enter your RainBird IQ4 account email and password
4. The integration will discover all controllers on your account

## Entities

| Entity Type | Description |
|---|---|
| Switch | One per program - toggle program on/off |
| Number | Seasonal adjustment percentage per program |
| Sensor | Rain delay (days) per controller |
| Binary Sensor | Controller connected status |
| Binary Sensor | Controller shutdown status |

## Tested Devices

| Device | Status |
|---|---|
| ESP-TM2 | Testing |

If you have tested this integration with a different controller, please open an issue or PR to update this list.

## Requirements

- A RainBird IQ4 cloud account (the same credentials used in the RainBird IQ4 mobile app)
- Controller with RainBird 2.0 firmware

## Dependencies

This integration uses the [pyiq4](https://github.com/tiagomota/pyiq4) Python library, which is an async port of the [rainbird-iq4-cli](https://github.com/nickustinov/rainbird-iq4-cli) Go CLI by [@nickustinov](https://github.com/nickustinov).

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to RainBird Corporation. Use at your own risk.

## License

MIT

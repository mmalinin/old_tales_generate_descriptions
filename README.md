# Project Title

## Overview

Generate markdown and wiki table files from Old tales config.xml

## Installation

To get started, ensure you have Python 3.10.11 and the following packages installed:

```sh
pip install lxml
```

## Usage

Generate tables using config from existing environment variable `GAME_CONFIG_PATH` or path passed as a first argument using `generate_texts` module.

Generate tables using autodetected steam library path using `generate_from_steam` module.
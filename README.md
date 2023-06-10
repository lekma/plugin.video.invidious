# Invidious for Kodi

An add-on for Kodi to watch content from [Invidious](https://invidious.io/).

![](https://user-images.githubusercontent.com/22801583/244897027-06bde28a-1fad-48bd-9aa2-e7cd63cf9870.png)

## Features

* Subscribe to channels locally, no account required.
* Browse Popular and Trending videos.
* Search for videos, channels, and playlists, with togglable search history.
* Instance selection available from within the add-on, displayed from the [publicly available instances](https://api.invidious.io/) list.
* Watch videos directly from YouTube, accessible from the context menu.

## Installation

### Method 1: Add Repository

First install [`repository.lekma`](https://github.com/lekma/repository.lekma/), which includes this add-on, and its dependencies.

Then install Invidious through the [Kodi interface](https://kodi.wiki/view/Add-on_manager#How_to_install_add-ons_from_a_repository), as you would any other extension.

### Method 2: Manual Installation

Alternatively, you can download the latest version from the [Releases](https://github.com/lekma/plugin.video.invidious/releases/) tab. If installing this way, you'll also need to install the dependencies manually:

* [`script.module.iapc`](https://github.com/lekma/script.module.iapc/releases/)
* [`script.module.yt-dlp`](https://github.com/lekma/script.module.yt-dlp/releases/)

## SponsorBlock

<img src="https://user-images.githubusercontent.com/22801583/244897045-a81a8a35-fd84-4692-96f9-0639578590f8.png" alt="" align="right"/>

You can install the third-party [Kodi SponsorBlock](https://github.com/siku2/script.service.sponsorblock/) add-on to automatically skip sponsored segments. It supports most of the features and API endpoints that the official browser extension does. 

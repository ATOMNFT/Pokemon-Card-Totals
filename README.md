# Pokémon Card Totals

A glassy yellow Docker widget showing ENG and JAP Pokémon card totals from TCGdex, with manual refresh, update timestamps, and persistent saved totals. Suitable for a dashboard iframe or Homarr embed.

## Install the published image

Download `docker-compose.yml` into its own folder, then run:

```bash
docker-compose up -d
```

Open http://localhost:8088 or http://YOUR-SERVER-IP:8088.
For a dashboard iframe, use http://YOUR-SERVER-IP:8088/?widget=1. Start with a tile around 400 × 280 pixels. Use an HTTPS reverse proxy URL when embedding on an HTTPS dashboard.

Images support Linux amd64 and arm64. Internet access to api.tcgdex.net is required; no API key is needed.

## Update

```bash
docker-compose pull
docker-compose up -d
```

Hard-refresh your browser after updating. Totals persist in the `totals-data` volume. Keep the same folder/project name to preserve that volume. `docker-compose down -v` deletes saved totals.

If switching from an earlier locally built version, replace the Compose file in the same installation folder with this one, then run the update commands above.

## Build from source

```bash
git clone https://github.com/ATOMNFT/Pokemon-Card-Totals.git
cd Pokemon-Card-Totals
docker-compose -f docker-compose.build.yml up -d --build
```

## What is counted?

Unique card IDs returned by the complete TCGdex English and Japanese card lists. Includes listed promos and secret rares. These are database totals, not your collection or a guaranteed exhaustive count of every physical printing. Finish and edition variants are not counted separately. Language coverage varies.

The first visit fetches totals; Refresh fetches again. If a language fails to refresh, its previous count and update time remain visible with an error.

## Publishing for maintainers

The GitHub Actions workflow tests the app and builds/publishes `ghcr.io/atomnft/pokemon-card-totals` on pushes to main, version tags (`v*`), or manual dispatch. Main publishes `latest`; version tags publish matching image tags. Each build also gets a commit SHA tag.

After the first successful run, open the package settings under your GitHub profile's Packages and change the package visibility to Public. A public repository alone does not make its container package public. Until this is done, anonymous pulls can fail.

Update source files on main to publish a new latest image. Users then run the update commands above. No personal access token needs to be stored for this workflow; it uses GitHub's built-in GITHUB_TOKEN.

## Development

Python 3.10+; no Python dependencies.

```bash
DATA_DIR=./data python app.py
python -m unittest discover -s tests -v
```

Pokémon is a trademark of its respective owners. This project is unofficial. Card data is supplied by TCGdex.

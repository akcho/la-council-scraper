# Deployment Guide

## Overview

The LA Council Tracker static site is deployed using GitHub Pages. The site is built from the `site/` directory.

## Deployment Options

### Option 1: GitHub Pages (Recommended)

GitHub Pages serves from a dedicated `gh-pages` branch.

**Quick Deploy:**

```bash
./deploy.sh
```

This will:
- Generate the site
- Create/update the `gh-pages` branch
- Copy site files to branch root
- Push to GitHub

**First-Time Setup:**

After running `./deploy.sh`, enable GitHub Pages:

1. Go to: https://github.com/YOUR-USERNAME/la-council-scraper/settings/pages
2. Source: Deploy from a branch
3. Branch: `gh-pages`
4. Folder: `/ (root)`
5. Save

Your site will be available at: `https://YOUR-USERNAME.github.io/la-council-scraper`

**Custom Domain (Optional):**
- Add a `CNAME` file to the `site/` directory with your domain name
- Run `./deploy.sh` to deploy
- Configure DNS to point to GitHub Pages

### Option 2: Netlify

1. Connect repository to Netlify
2. Build settings:
   - Build command: `python generate_site.py`
   - Publish directory: `site`
3. Deploy

### Option 3: Vercel

1. Connect repository to Vercel
2. Build settings:
   - Build command: `pip install -r requirements.txt && python generate_site.py`
   - Output directory: `site`
3. Deploy

## Site Generation

Generate the static site:

```bash
python generate_site.py
```

This will:
- Read all parsed agendas from `data/agendas/`
- Generate individual meeting pages in `site/meetings/`
- Generate the index page at `site/index.html`

## Analytics Configuration

Edit `site_config.json` to add your analytics domain:

```json
{
  "analytics": {
    "provider": "plausible",
    "domain": "your-domain.com"
  }
}
```

Then regenerate the site with `python generate_site.py`.

## Workflow

1. Run the pipeline to fetch new meetings and parse agendas:
   ```bash
   python run_pipeline.py
   ```

2. Deploy to GitHub Pages:
   ```bash
   ./deploy.sh
   ```

That's it! The script handles generation and deployment automatically.

## Directory Structure

```
site/
  index.html          # Homepage with meeting list
  meetings/
    17432.html        # Individual meeting pages
    17455.html
    ...
```

## Notes

- The `site/` directory is included in git (see `.gitignore`)
- Templates are in `templates/` directory
- Site configuration is in `site_config.json`
- Generated pages are mobile-first responsive design

# Engineering Portfolio

Static portfolio website for Aditya Kashyap (mechanical / aerospace / gas-turbine MRO).
Built from the existing `index_template.html` — the original template and every file under
`engineering_projects/` are untouched; this `Portfolio/` folder is entirely new.

## Folder structure

```
Portfolio/
├── index.html                  # main page (copied from ../index_template.html, then modified)
├── README.md                   # this file
├── assets/
│   ├── css/style.css           # extracted stylesheet (was inline <style>)
│   ├── js/script.js            # extracted script (was inline <script>: gears + reveal)
│   └── images/                 # optional local images (pic1.jpeg resolves here; fallback initials shown if missing)
└── projects/
    └── landing-gear-dynamics/
        ├── index.html          # project detail page (reads results/results.json)
        ├── landing_gear.py     # copy of engineering_projects/Landing_gear_dynamics/landing_gear_final.py
        ├── requirements.txt    # numpy, scipy, matplotlib, pillow
        ├── README.md           # how to run the simulation
        └── results/            # generated outputs (do not edit by hand)
            ├── 1_design_comparison.png
            ├── 2_energy_accounting.png
            ├── 3_robustness.png
            ├── landing_gear_animation.gif
            ├── scenario_results.csv
            └── results.json    # live metrics consumed by index.html
```

## How the website reads its results

`projects/landing-gear-dynamics/index.html` fetches `results/results.json` with a **relative**
path (`fetch("results/results.json")`) — no leading `/`, no absolute URL. That keeps the page
working both locally and on GitHub Pages (which serves the repo from a sub-path).

On load it renders:
- nominal design-landing metrics (peak force / stroke utilisation / margin) per design,
- the 120-case Monte Carlo summary table,
- the off-design scenario table,
- verification checks, generated timestamp, and file list,
- the three PNGs and the animation GIF from the same `results/` folder.

So to refresh the page: just re-run the simulation (below) — the page always shows the
latest `results.json`. No hand-editing of numbers anywhere.

## Run locally

No build step or server is required. Open `Portfolio/index.html` in a browser.
For `results.json` to load over `file://`, a browser may block the fetch; if so, serve the
folder with any static server, e.g. `python -m http.server` from inside `Portfolio/`.

## Publishing (manual, later)

Upload the `Portfolio/` folder to GitHub as-is and enable GitHub Pages on it. Because all
links and asset paths are relative (`assets/...`, `projects/...`, `results/...`), the site
works from any repository sub-path without configuration changes.

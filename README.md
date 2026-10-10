# Supermenu

Pick three objects from a case of twelve; the page answers with one task from the Personal Inventory deck,
laid out as an A4 sheet to do the task on, tick (Done / Not for me) and, if wanted, photograph with #supermenuARS.

- `site/index.html` is the whole page, ready for Netlify. Drag the `site` folder onto the site's Deploys page.
- `template.html` holds the page; `data.json` the 29 objects (with their operation), the operations map and the 30 tasks.
- `decoder.html` reads the code on a returned sheet (SM- and four characters): the three objects in the order picked and the task. For you only, as it names the operations; it is not part of `site`. Open it from disk.
- `codec.js` is how codes are made and read; both pages use it.
- `python3 build.py` rebuilds `site/index.html` (plus `decoder.html`, and `supermenu.html`, the private preview on claude.ai) after any change.

Data comes from the game: `game/prototypes/labyrinth/content/object_ops.json`, `data/decks.json` (deck `inv`),
`content/tags.json` and `data/operations.json`, with images from `game/assets/objects/`. Nothing a visitor picks is stored.
Before a wider launch: full credits for each object (museum, object, licence).

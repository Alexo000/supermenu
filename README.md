# Supermenu

Two ways in:
- **The case**: twelve objects drawn at random; pick three; the page answers with one task.
- **Full view** (`#full` opens it directly): all the objects; pick six, nine or twelve; the page reads them in
  threes, in the order picked, and gives each three its closest task that no other three has taken.

Each task comes as an A4 sheet to do it on, tick (Done / Not for me) and, if wanted, photograph with
#supermenuARS. Each sheet carries a code that records its three objects and its task.

Supermenu stands on its own. It shares no files with the game (Shubyrinth): its objects, tasks and
operations are its own copies, made on 2026-10-11, and can change without touching the game, or the other way round.

## Files

- `source/objects.json` and `source/objects/` hold the 248 cut-out objects. An object appears only when it has
  an `op` (191 do). 1 to 157 come from the COSMORAMA Supermenu; `excluded: true` marks the 57 of those kept out:
  modern artworks and designs, machines, human remains, portraits of real people. 158 to 248 are archive picks
  (public domain or CC0), with the museum page in `source` and its credit line and licence in `credit`.
  `why` is a note for you; `title` and `credit` are for the credits.
- `source/tasks.json` holds the 30 tasks (English and Spanish) and the chain of operations each carries.
- `source/operations.json` holds the operations, with their place on the map (`xy`) and family (`cat`),
  which the engine uses to find the closest task.
- `source/codes.json` holds the code versions (see below). Never edit or remove a version.
- `template.html` is the page; `codec.js` makes and reads the sheet codes; `decoder_template.html` is the decoder.
- `python3 build.py` rebuilds everything below after any change. It stops and says what is wrong if an
  object or task names an operation it does not know.
- `site/index.html` is the whole page. GitHub Pages publishes the `site` folder at https://alexo000.github.io/supermenu/
  each time a change to it is pushed to GitHub (`.github/workflows/pages.yml`). The code lives at github.com/Alexo000/supermenu.
- `decoder.html` reads the codes on returned sheets: the three objects and the task. For you only, as it names
  the operations; it is not part of `site`. Open it from disk.
- `embed.html` is the snippet for a Squarespace Code block: the page sets its own height on the host page
  (no inner scroll bar on phones) and scrolls it to the sheets. Printing from inside the embed opens the sheets
  in their own tab (`?print#CODE.CODE`) and prints there, one sheet per page.

## Codes

Each version of the code counts against a fixed list of objects and tasks, so printed sheets always read back.
- `SM-` and four characters: the first 29 objects, three in the order picked (10 October 2026).
- `SM2-` and five characters: the 100 objects, three kept as a set (11 October 2026).
- `SM3-` and six characters: the 191 objects, three kept as a set (11 October 2026, with the archive picks).
When the objects or tasks change, `build.py` adds the next version (`SM3-`, …) by itself and says so.

Nothing a visitor picks is stored.

The archive search and the picking of new objects live in `research/`: `search.py` finds candidates,
`make_review.py` makes the page to choose them, `fetch_large.py` gets bigger pictures, `cutout.py` cuts them out,
`add_objects.py` added the 91 picks of 11 October 2026. Before a wider launch: full credits for each object (museum, object, licence),
or replacement by open-licence images (see the archive search plan).

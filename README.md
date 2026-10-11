# Supermenu

Pick three objects from a case of twelve; the page answers with one task, laid out as an A4 sheet to do the
task on, tick (Done / Not for me) and, if wanted, photograph with #supermenuARS. Each sheet carries a code
(SM- and four characters) that records the three objects and the task.

Supermenu stands on its own. It shares no files with the game (Shubyrinth): its objects, tasks and
operations are its own copies, made on 2026-10-11, and can change without touching the game, or the other way round.

## Files

- `source/objects.json` and `source/objects/` hold the 157 cut-out objects. An object appears in the case
  only when it has an `op` (29 do now). `why` is a note for you; `title` and `credit` are for the credits.
- `source/tasks.json` holds the 30 tasks (English and Spanish) and the chain of operations each carries.
- `source/operations.json` holds the operations, with their place on the map (`xy`) and family (`cat`),
  which the engine uses to find the closest task.
- `template.html` is the page; `codec.js` makes and reads the sheet codes; `decoder_template.html` is the decoder.
- `python3 build.py` rebuilds everything below after any change. It stops and says what is wrong if an
  object or task names an operation it does not know.
- `site/index.html` is the whole page, ready for Netlify: drag the `site` folder onto the site's Deploys page.
- `decoder.html` reads the code on a returned sheet: the three objects in the order picked and the task.
  For you only, as it names the operations; it is not part of `site`. Open it from disk.
- `embed.html` is the snippet for a Squarespace Code block: the page sets its own height on the host page
  (no inner scroll bar on phones) and scrolls it to the sheet. Printing from inside the embed opens the sheet
  in its own tab (`?print#SM-XXXX`) and prints there.

## Codes

Codes depend on which objects are in the case and on the tasks. Adding, removing or reordering either
changes what new codes mean, and old sheets would decode wrongly. When that happens, move to `SM2-` codes
(see `codec.js`) so both versions can be read.

Nothing a visitor picks is stored. Before a wider launch: full credits for each object (museum, object, licence).

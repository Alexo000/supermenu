# Brief for Claude Code: more archives for research/search.py

Alejandro wants the candidates to come from a wider set of museums. The Met (fixed: v1.1 search) and the
Wellcome Collection are now in the script, but neither has been run live yet. Please run them first, then add
the archives below. Each one needs trying against the live site, which only a machine with ordinary internet can do.

## Rules for every source
- Keep only images that are public domain, the public domain mark, or CC0. Drop anything CC BY, non-commercial or unknown.
- Each source is a function `name(term, per) -> list of dicts` with the same keys as `met()`:
  source, id, title, kind, culture, date, material, licence, credit, page, image (a picture about 400 px wide).
- Register it in `SOURCES`. Never send anything but the search words (and an API key where one is needed).
- Keys go in environment variables, never in the file: `SI_API_KEY` (Smithsonian, free at api.data.gov),
  `EUROPEANA_KEY` (free; try `api2demo` first). With no key set, that source is skipped with a note.
- Test each one alone, small: `python3 research/search.py --source <name> --row seals --per 2`.
  Look at two or three of the pictures it saved before moving on.

## Sources to add, in this order
1. **Met**: run `--source met --row seals --per 2`. The v1.1 search should answer; if the response shape
   differs from `{"total":…, "objectIDs":[…]}`, adjust.
2. **Wellcome**: run `--source wellcome --row tools --per 2`. Check the thumbnail URL becomes a working IIIF image.
3. **Rijksmuseum** (no key): the keyless search at `https://data.rijksmuseum.nl/search/collection`
   (parameters such as `type`, `description`, `creator`, `imageAvailable=true`; Dutch words work better than
   English, e.g. `sleutel` for key, `zegel` for seal, `speelgoed` for toy). Results are Linked Art identifiers:
   follow each to its record to find the title, date and the IIIF image. Check the licence is public domain or CC0.
4. **SMK, Copenhagen** (no key): `https://api.smk.dk/api/v1/art/search/` with `keys`, `rows` and filters for
   `has_image` and `public_domain`. Use the thumbnail it gives.
5. **Europeana** (key; try `api2demo`): `https://api.europeana.eu/record/v2/search.json` with `qf=TYPE:IMAGE`
   and a rights filter that keeps only public domain and CC0 (check `rights` on each item for
   `publicdomain/mark` or `publicdomain/zero`; `reusability=open` alone also lets CC BY through).
   Credit = the item's `dataProvider`. This one brings in many smaller European museums.
6. **Smithsonian** (key `SI_API_KEY`): `https://api.si.edu/openaccess/api/v1.0/search` with
   `online_media_type:Images` in the query; keep media whose `usage.access` is `CC0`.

## Balance
After the sources work, run the whole search again (`python3 research/search.py`). The script prints a table of
candidates by row and archive at the end. If one archive gives more than half of any row, lower `--per` for it or
rerun that row with `--source` for the others. Then tell Alejandro the table, the problems list, and anything you
changed in the script, so he can pass it back to the Supermenu chat for the contact sheets.

Commit the script when it works, with a short message.

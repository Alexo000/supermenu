#!/usr/bin/env python3
"""One-off (2026-10-11): adds the 91 archive picks to source/ as objects 158-248, with drafted operations.

Run from the supermenu folder: python3 research/add_objects.py  (safe to run twice: it skips objects already added).
"""
import csv, json, pathlib, shutil
from PIL import Image
# picks order (research/picks.csv) -> (op, why). Draft by Claude for Alejandro to correct.
D = [
("SUBSTITUTE","a name cut in reverse, to stand in for its owner"),        # 1 Seal, Korea
("ITERATE","rolled again and again, one band of pattern"),                 # 2 Cylindrical seal, Tlatilco
("ALTERNATE","the scarab turns: beetle side, seal side"),                  # 3 Ring with scarab bezel
("SUBSTITUTE","a small brass shape standing in for a sum of gold"),        # 4 Goldweight, geometric shape
("LOCATE","it tells the time only once it knows where north is"),         # 5 Compass sundial
("RANK","one step in a ladder of weights"),                                # 6 Goldweight, geometric design
("DIFFER FROM EACH","each glass head made in its own colours"),            # 7 Pendant head, Carthage
("CALIBRATE","the pan is checked against the weights, not by eye"),        # 8 Box with scale and weights
("DEFER","the oracle answers and the answer is obeyed"),                   # 9 Divination implement, Luba
("CONTAIN","a figure holds up the bowl that holds the nuts"),             # 10 Ifa divination vessel
("RANK","the king carved largest, the others smaller"),                    # 11 Veranda post
("GRAFT","a key and a pistol made into one tool"),                         # 12 Door key with pistol
("ACCUMULATE","one bead more, never a choice"),                            # 13 String of glass beads
("STRIP","the arms gone, the stance still holds"),                         # 14 Male deity
("SATURATE","beads and feathers over every inch"),                         # 15 Wedding basket
("RANK","drawers graded from deep to shallow"),                            # 16 High chest of drawers
("CONCEAL","a lock on show; what it guards is not"),                       # 17 Casket, Sicily
("PARTITION","each face divided into its own panels"),                     # 18 Casket, Venice
("MIMIC","a small person"),                                                # 19 Doll, Ibibio
("SAMPLE","a torso kept as a whole of its own"),                           # 20 Torso from a doll
("SUSPEND THE RULES","whoever wears it stops being themself while it is on"), # 21 Chihongo mask
("CONTAIN","a flower held whole inside the glass"),                        # 22 Paperweight
("TRANSLATE","a cat carried into bronze, holes and all"),                  # 23 Feline incense burner
("EXHAUST","every surface worked, the plain ones too"),                    # 24 Luxury ewer
("MORPH","a jug that has turned into a bird"),                             # 25 Bird-shaped vessel
("NAME","one particular face, not a type"),                                # 26 Portrait head vessel
("OCCUPY","sits and stays"),                                               # 27 Seated deity
("FOREGROUND","the headdress takes over from the face"),                   # 28 Head of Xilonen
("COUPLE","bell in one hand, thunderbolt in the other, never apart"),      # 29 Vajrasattva
("SCAFFOLD","blown into a mould that was then taken away"),                # 30 Bottle, Syria
("SUBSTITUTE","a lizard where the handle was"),                            # 31 Covered ewer
("MIMIC","glass passing as a date"),                                       # 32 Flask shaped like a date
("EXAGGERATE","ears and trunk as long panels"),                            # 33 Elephant mask
("LAY OVER","feathers laid row over row on the cloth"),                    # 34 Feathered tabard
("RITUALISE","tea measured out the same way each day"),                    # 35 Tea caddy
("DEFER","the throw decides"),                                             # 36 Dice figures
("TRACE","the mend shows where the break ran"),                            # 37 Bowl, mended
("EXECUTE","someone carried on what the maker began"),                     # 38 Statuette, mended
("CONSTRAIN","one mark only, however you press"),                          # 39 Seal, Iran
("GRAFT","a scent bottle and a seal in one"),                              # 40 Scent bottle with seal
("RUN IT LONG","rolled further, the picture just goes on"),                # 41 Cylinder seal, crystal
("JUXTAPOSE","two pictures side by side, no caption"),                     # 42 Stamp seal, two motifs
("REPLICATE","one bird made twice"),                                       # 43 Stamp seal, two birds
("ALTERNATE","crosses and bands in turn"),                                 # 44 Cylinder seal, stone
("GENERALISE","a rule of weight cast in bronze"),                          # 45 Balance weight
("HALVE","each cup half the one it sits in"),                              # 46 Nested cup weights
("ELICIT","its use has to be guessed from its shape"),                     # 47 Breeding jug or scabbard
("TRIANGULATE","rings from three directions meet at one point"),           # 48 Armillary sundial
("EXHAUST","every count kept on a stick"),                                 # 49 Abacus
("SAMPLE","a piece of a measure, standing alone"),                         # 50 Measuring rod fragment
("CALIBRATE","the length others were checked against"),                    # 51 Cubit rod fragment
("DEFER","a bone thrown to decide"),                                       # 52 Dice, bone
("COUPLE","three dice tied, thrown together"),                             # 53 Dice on a string
("LEASE","the square is yours only until the next move"),                  # 54 Gaming piece
("DON'T REPEAT YET","the answer cannot be asked for again at once"),       # 55 Divination vessel, Edo
("ELICIT","tapped to call the answer up"),                                 # 56 Ifa tapper
("HAND OVER","holds the bowl out to whoever comes"),                       # 57 Agere Ifa, kneeling woman
("CONCEAL","ink kept under a turtle's shell"),                             # 58 Inkstone, turtle
("PARTITION","decides who is on which side of the door"),                  # 59 Key
("CONSTRAIN","shut, and only one way to open it"),                         # 60 Padlock
("DISPERSE","two keys, either will do"),                                   # 61 Padlock with two keys
("LEASE","locked until someone comes back with the key"),                  # 62 Padlock, Sweden
("EXCHANGE","a promise to pay, passed hand to hand"),                      # 63 Token money
("FIND THE THRESHOLD","how little of a bowl is still a bowl"),             # 64 Bowl sherd
("DISSOLVE AND REBUILD","broken into pieces, put back from the pieces"),   # 65 Head with helmet
("TRANSLATE","a stage face carried into clay"),                            # 66 Comic mask
("EXECUTE","finished again by a later hand"),                              # 67 Seated boy
("ATTEND","eyes up, collecting nothing"),                                  # 68 Sculpture, head
("RUN IT LONG","lit, it goes on until the oil runs out"),                  # 69 Lamp
("BUILD ON THE MARKS","each coil sits on the one before"),                 # 70 Basket
("ACCUMULATE","the odds and ends of a trade, kept"),                       # 71 Cobbler box
("CLASSIFY","medallions set out in rows"),                                 # 72 Casket, 1875
("PARTITION","inside, a place for each thing"),                            # 73 Toilet case
("DEGRADE","rusted to where it is barely a box"),                          # 74 Casket, Sweden
("LOCATE","raised on legs, it sets its own place"),                        # 75 Ivory casket
("SATURATE","lace-fine metal over every face"),                            # 76 Cabinet
("GENERALISE","not one house, a house"),                                   # 77 House model
("MIMIC","a person, hand-sized"),                                          # 78 Toy figure
("STRIP","a body down to its outline"),                                    # 79 Doll, Sasanian
("EXAGGERATE","horns too wide, still a buffalo"),                          # 80 Doll (buffalo)
("MARK TIME","a drummer keeping the beat"),                                # 81 Miniature drummer
("GENERALISE","a bird reduced to the idea of one"),                        # 82 Bird figure
("SUSPEND THE RULES","worn for the time the ordinary rules are off"),      # 83 Hook mask
("NAME","one ancestor, by name, over the door"),                           # 84 Tekoteko
("RITUALISE","worn the same way, at set times"),                           # 85 Headdress for scholars
("ATTEND","sits and watches, takes nothing"),                              # 86 Monkey
("RUN IT LONG","built to walk for days"),                                  # 87 Bactrian camel
("FOREGROUND","the inside shows through and becomes the subject"),         # 88 Glass jug
("SAMPLE","a face cut out of a larger piece"),                             # 89 Roman bone carving
("GRAFT","parts of different creatures made into one"),                    # 90 Tupilaq
("RELOCATE","a temple moved onto a table"),                                # 91 Temple model
]

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / 'source'


def main():
    ops = json.loads((SRC / 'operations.json').read_text(encoding='utf-8'))
    bad = sorted({op for op, _ in D if op not in ops})
    if bad:
        raise SystemExit(f'unknown operations: {bad}')
    with (HERE / 'picks.csv').open(encoding='utf-8') as f:
        picks = list(csv.DictReader(f))
    with (HERE / 'candidates.csv').open(encoding='utf-8') as f:
        cand = {f"{r['source']}:{r['id']}": r for r in csv.DictReader(f)}
    assert len(picks) == len(D), (len(picks), len(D))
    data = json.loads((SRC / 'objects.json').read_text(encoding='utf-8'))
    objs = data['objects']
    have = {o['source'] for o in objs}
    nxt = max(o['id'] for o in objs) + 1
    added = 0
    for p, (op, why) in zip(picks, D):
        r = cand[p['key']]
        source = f"{r['source']}, {r['page']}"
        if source in have:
            continue
        stem = pathlib.Path(r['file']).stem
        cut = HERE / 'cutouts' / (stem + '.webp')
        name = f'objects/{nxt:03d}.webp'
        shutil.copyfile(cut, SRC / name)
        w, h = Image.open(cut).size
        credit = '; '.join(x for x in (r['credit'].strip().rstrip(','), r['licence']) if x)
        objs.append({'id': nxt, 'file': name, 'width': w, 'height': h, 'op': op, 'why': why,
                     'source': source, 'title': r['title'], 'credit': credit, 'excluded': False})
        nxt += 1; added += 1
    data['note'] = data['note'].rstrip() + ('' if 'archive picks' in data['note'] else
        " Objects from 158 on are archive picks (2026-10-11): public domain or CC0, cut out from museum open-access "
        "pictures; 'source' gives the museum page, 'credit' the museum's credit line and licence.")
    (SRC / 'objects.json').write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{added} objects added; ids now run to {nxt - 1}')


if __name__ == '__main__':
    main()

"""Build the Philippine location data (PSGC) used by the Province > City > Barangay selector.

Run once (needs internet):   python tools/build_psgc.py
Writes static/data/psgc/provinces.json and one static/data/psgc/<province code>.json per
province ({"City name": ["Barangay", ...]}). Data: https://psgc.gitlab.io/api (PSA PSGC).
"""
import json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = 'https://psgc.gitlab.io/api/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'data', 'psgc')
NCR = 'NCR'  # pseudo-province code: Metro Manila has no provinces, only cities


def get(path, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(API + path + '.json', timeout=40) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise


def main():
    provinces = get('provinces')
    cities = get('cities-municipalities')
    by_name = {p['name']: p['code'] for p in provinces}
    groups = {p['code']: [] for p in provinces}
    groups[NCR] = []
    leftovers = {'City of Isabela': 'Basilan', 'City of Cotabato': 'Maguindanao'}
    for c in cities:
        pc = c['provinceCode']
        if not pc:
            pc = NCR if c['districtCode'] else by_name.get(leftovers.get(c['name']))
        if not pc or pc not in groups:
            print('unplaced:', c['name'], file=sys.stderr)
            continue
        groups[pc].append(c)

    todo = [c for g in groups.values() for c in g]
    print(len(todo), 'cities/municipalities; fetching barangays...')
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(lambda c: get('cities-municipalities/%s/barangays' % c['code']), todo))
    brgys = {c['code']: sorted({b['name'] for b in r}, key=str.lower) for c, r in zip(todo, res)}

    os.makedirs(OUT, exist_ok=True)
    index = []
    for p in sorted(provinces, key=lambda p: p['name']) + [{'code': NCR, 'name': 'Metro Manila'}]:
        g = sorted(groups[p['code']], key=lambda c: c['name'].lower())
        if not g:
            continue
        data = {c['name']: brgys[c['code']] for c in g}
        with open(os.path.join(OUT, p['code'] + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        index.append({'n': p['name'], 'c': p['code']})
    index.sort(key=lambda x: x['n'].lower())
    with open(os.path.join(OUT, 'provinces.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    print('done:', len(index), 'provinces,', sum(len(v) for v in brgys.values()), 'barangays')


if __name__ == '__main__':
    main()

"""Match hospital names in the 2025 data to named OSM healthcare places.

Usage: python -m scripts.build_hospital_map /path/to/kazakhstan.osm.pbf
The OSM extract is not committed. The generated JSON contains only accepted,
unique matches and keeps the OSM object ID for review.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import osmium
import pandas as pd
from rapidfuzz import fuzz, process
from shapely.geometry import Point, shape


ROOT = Path(__file__).resolve().parents[1]
HOSPITAL_DATA = ROOT / "data/processed/hospital_day.parquet"
MAP_DATA = ROOT / "frontend/src/pages/welcome/model/hospitalCoordinates.json"
REVIEW_DATA = ROOT / "data/processed/hospital_map_review.json"
MEDICAL_AMENITIES = {"hospital", "clinic", "doctors", "health_post"}
MEDICAL_HEALTHCARE = {"hospital", "clinic", "doctor", "centre", "center", "polyclinic", "rehabilitation"}
NAME_TAGS = ("name:ru", "name", "official_name:ru", "official_name", "short_name:ru", "short_name", "alt_name:ru", "alt_name", "name:kk")
LEGAL_PREFIX = re.compile(
    r"^(?:(?:государственн\w*|коммунальн\w*|казенн\w*|предприяти\w*|учреждени\w*|"
    r"на|праве|хозяйственн\w*|ведени\w*|акционерн\w*|общество|"
    r"республиканск\w*|товарищество|ограниченн\w*|ответственност\w*|"
    r"гкп|гкппхв|кгп|кгкп|ао|тоо|ргп)\s+)+",
)
KAZAKH_LETTERS = str.maketrans("әғқңөұүһіё", "агкноуухие")
OWNER_SUFFIX = re.compile(
    r"\b(?:управлени\w*\s+здравоохранени\w*|на\s+праве\s+хозяйственн\w*|"
    r"при\s+государственн\w*|акимата\s+города)\b"
)
REGION_HINTS = (
    ("западно казахстанск", "Западно-Казахстанская область"),
    ("восточно казахстанск", "Восточно-Казахстанская область"),
    ("северо казахстанск", "Северо-Казахстанская область"),
    ("акмолинск", "Акмолинская область"),
    ("актюбинск", "Актюбинская область"),
    ("алматинск", "Алматинская область"),
    ("атырауск", "Атырауская область"),
    ("жамбылск", "Жамбылская область"),
    ("жетису", "Жетысуская область"),
    ("карагандинск", "Карагандинская область"),
    ("костанайск", "Костанайская область"),
    ("кызылординск", "Кызылординская область"),
    ("мангистауск", "Мангистауская область"),
    ("павлодарск", "Павлодарская область"),
    ("туркестанск", "Туркестанская область"),
    ("улытауск", "Улутауская область"),
    ("области абай", "Абайская область"),
    ("область абай", "Абайская область"),
    ("города шымкент", "Шымкент"),
    ("города алматы", "Алматы"),
    ("города астан", "Астана"),
)


def normalize(value: str) -> str:
    value = value.lower().translate(KAZAKH_LETTERS)
    value = value.replace("№", " номер ")
    value = re.sub(r"[^\w\d]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def hospital_name(value: str) -> str:
    first_quote = min((pos for pos in (value.find('"'), value.find('«')) if pos >= 0), default=-1)
    if first_quote >= 0:
        value = value[first_quote + 1 :]
    owner = OWNER_SUFFIX.search(value.lower())
    if owner:
        value = value[:owner.start()]
    value = LEGAL_PREFIX.sub("", value.lower())
    return normalize(value)


def osm_name_variants(value: str) -> set[str]:
    full = normalize(value)
    without_prefix = normalize(LEGAL_PREFIX.sub("", value.lower()))
    return {variant for variant in (full, without_prefix) if len(variant) >= 12}


def hospital_region(name: str) -> str | None:
    value = normalize(name)
    return next((region for hint, region in REGION_HINTS if hint in value), None)


@dataclass(frozen=True)
class Place:
    osm_id: str
    names: tuple[str, ...]
    longitude: float
    latitude: float
    address: str


class MedicalPlaces(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.places: list[Place] = []
        self.regions: list[tuple[str, object]] = []
        self.geojson_factory = osmium.geom.GeoJSONFactory()

    def area(self, area) -> None:
        if area.tags.get("boundary") != "administrative" or area.tags.get("admin_level") != "4":
            return
        try:
            geometry = shape(json.loads(self.geojson_factory.create_multipolygon(area)))
        except (ValueError, RuntimeError):
            return
        name = area.tags.get("name:ru") or area.tags.get("name")
        if name and not geometry.is_empty:
            self.regions.append((name, geometry))

    def region_at(self, place: Place) -> str | None:
        point = Point(place.longitude, place.latitude)
        matches = [name for name, geometry in self.regions if geometry.covers(point)]
        return next((name for name in matches if "область" not in name), matches[0] if matches else None)

    def _add(self, kind: str, obj, longitude: float, latitude: float) -> None:
        tags = obj.tags
        if tags.get("amenity") not in MEDICAL_AMENITIES and tags.get("healthcare") not in MEDICAL_HEALTHCARE:
            return
        names = tuple(dict.fromkeys(tags.get(key) for key in NAME_TAGS if tags.get(key)))
        if not names:
            return
        address = ", ".join(
            part for part in (
                tags.get("addr:city", ""),
                tags.get("addr:street", ""),
                tags.get("addr:housenumber", ""),
            ) if part
        )
        self.places.append(Place(f"{kind}/{obj.id}", names, longitude, latitude, address))

    def node(self, node) -> None:
        if node.location.valid():
            self._add("node", node, node.location.lon, node.location.lat)

    def way(self, way) -> None:
        points = [(node.location.lon, node.location.lat) for node in way.nodes if node.location.valid()]
        if points:
            self._add(
                "way", way,
                sum(point[0] for point in points) / len(points),
                sum(point[1] for point in points) / len(points),
            )


def build_index(places: list[Place]) -> dict[str, set[int]]:
    index: dict[str, set[int]] = defaultdict(set)
    for number, place in enumerate(places):
        for name in place.names:
            for variant in osm_name_variants(name):
                index[variant].add(number)
    return index


def candidates_for(name: str, index: dict[str, set[int]], keys: list[str]) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    variant = hospital_name(name)
    for key, score, _ in process.extract(variant, keys, scorer=fuzz.ratio, limit=12, score_cutoff=74):
        for place_number in index[key]:
            scores[place_number] = max(scores.get(place_number, 0), score)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:8]


def near_same_place(first: Place, second: Place) -> bool:
    return abs(first.longitude - second.longitude) < 0.002 and abs(first.latitude - second.latitude) < 0.002


def match_hospital(
    name: str,
    places: MedicalPlaces,
    index: dict[str, set[int]],
    keys: list[str],
) -> tuple[dict | None, dict]:
    candidates = candidates_for(name, index, keys)
    expected_region = hospital_region(name)
    if expected_region:
        candidates = [
            (number, score) for number, score in candidates
            if places.region_at(places.places[number]) == expected_region
        ]
    review = {
        "hospital": name,
        "expected_region": expected_region,
        "candidates": [
            {"osm_id": places.places[number].osm_id, "name": places.places[number].names[0], "score": round(score, 1)}
            for number, score in candidates[:3]
        ],
    }
    if not candidates:
        return None, review

    best_number, best_score = candidates[0]
    best = places.places[best_number]
    competitors = [
        score for number, score in candidates[1:]
        if not near_same_place(best, places.places[number])
    ]
    margin = best_score - max(competitors, default=0)
    primary_score = fuzz.ratio(hospital_name(name), normalize(best.names[0]))
    # Exact name matches still need to be unique across distinct facilities.
    if best_score < 96 or margin < 10 or primary_score < 90:
        review["reason"] = "name or location is ambiguous"
        return None, review
    if not expected_region and len(hospital_name(name).split()) < 3:
        review["reason"] = "short name without a region"
        return None, review

    return {
        "name": name,
        "coordinates": [round(best.longitude, 6), round(best.latitude, 6)],
        "osm_id": best.osm_id,
        "osm_name": best.names[0],
        "address": best.address,
        "region": places.region_at(best),
        "score": round(best_score, 1),
    }, review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pbf", type=Path, help="Kazakhstan OSM PBF extract")
    args = parser.parse_args()

    places = MedicalPlaces()
    places.apply_file(str(args.pbf), locations=True, idx="flex_mem")
    hospitals = sorted(pd.read_parquet(HOSPITAL_DATA, columns=["hospital_mo"])["hospital_mo"].dropna().unique())
    index = build_index(places.places)
    keys = list(index)
    matches = []
    review = []
    for name in hospitals:
        match, result = match_hospital(name, places, index, keys)
        if match:
            matches.append(match)
        else:
            review.append(result)

    by_osm_id: dict[str, list[dict]] = defaultdict(list)
    for match in matches:
        by_osm_id[match["osm_id"]].append(match)
    unique_matches = [match for match in matches if len(by_osm_id[match["osm_id"]]) == 1]
    for match in matches:
        if len(by_osm_id[match["osm_id"]]) > 1:
            review.append({"hospital": match["name"], "reason": "same OSM place matched to multiple hospitals", "candidates": [{"osm_id": match["osm_id"], "name": match["osm_name"], "score": match["score"]}]})

    MAP_DATA.write_text(json.dumps(unique_matches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REVIEW_DATA.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Regions:", ", ".join(name for name, _ in places.regions))
    print(f"OSM places: {len(places.places)}; hospitals: {len(hospitals)}; matches: {len(unique_matches)}; review: {len(review)}")


if __name__ == "__main__":
    main()

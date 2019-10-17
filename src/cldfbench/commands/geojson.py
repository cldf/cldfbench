"""
Write a geoJSON file, mapping the languages in the dataset, to the Dataset's directory.
"""
import collections

from clldutils import jsonlib

from cldfbench.cli_util import add_dataset_spec, get_dataset


def register(parser):
    add_dataset_spec(parser)


def run(args):
    ds = get_dataset(args)
    languages_with_coordinates = {}
    for spec in ds.cldf_specs_dict.values():
        cldf = spec.get_dataset()
        try:
            id_ = cldf['LanguageTable', 'id']
            lat = cldf['LanguageTable', 'latitude']
            lon = cldf['LanguageTable', 'longitude']
        except KeyError:
            continue
        for language in cldf['LanguageTable']:
            if language[lat.name]:
                languages_with_coordinates[language.pop(id_.name)] = (
                    float(language.pop(lat.name)),
                    float(language.pop(lon.name)),
                    language)
    geojson = {"type": "FeatureCollection", "features": []}
    for id, (lat, lon, props) in languages_with_coordinates.items():
        geojson['features'].append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": collections.OrderedDict([
                (k, v) for k, v in props.items() if v]),
        })
    jsonlib.dump(geojson, ds.dir / 'languages.geojson', indent=2)

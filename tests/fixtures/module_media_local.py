from cldfbench import Dataset, CLDFSpec


class t_a:
    name = 'origin'
    url = 'https://github.com/lexibank/dataset.git'


class t_b:
    remotes = [t_a()]


class t_c:
    repo = t_b()
    url = 'https://github.com/lexibank/dataset.git'

    def json_ld(self):
        pass  # pragma: no cover


class Thing(Dataset):
    id = 'medialocal'
    repo = t_c()

    def cldf_specs(self):  # pragma: no cover
        return {None: Dataset.cldf_specs(self)}

    def cmd_makecldf(self, args):  # pragma: no cover
        args.writer.cldf.add_component('MediaTable')
        args.writer.objects['MediaTable'].append(
            {'ID': '12345', 'Download_URL': 'Generic-metadata.json', 'Media_Type': 'application/json'}
        )
        args.writer.objects['MediaTable'].append(
            {'ID': '12345', 'Download_URL': 'Generix-metadata.json', 'Media_Type': 'application/json'}
        )

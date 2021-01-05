from cldfbench import Dataset, CLDFSpec


class t_a(object):
    name = 'origin'
    url = 'https://github.com/lexibank/dataset.git'


class t_b(object):
    remotes = [t_a()]


class t_c(object):
    repo = t_b()
    url = 'https://github.com/lexibank/dataset.git'

    def json_ld(self):
        pass  # pragma: no cover


class Thing(Dataset):
    id = 'thing'
    repo = t_c()

    def cldf_specs(self):  # pragma: no cover
        return {
            None: Dataset.cldf_specs(self),  # The default spec
            'structure': CLDFSpec(dir=self.cldf_dir, module='StructureDataset'),
        }

    def cmd_makecldf(self, args):  # pragma: no cover
        with self.cldf_writer(args) as w:
            w.cldf.add_table('media.csv', {
                'name': 'ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
                'valueUrl': 'https://cdstar.shh.mpg.de/bitstreams/{objid}/{fname}',
                },
                'objid', 'fname', 'mimetype',
                {'name': 'size', 'datatype': 'integer'}, primaryKey=['ID'])
            w.write(
                **{'media.csv': [
                    {'ID': '12345', 'objid': 'foo', 'fname': '12345.wav', 'mimetype': 'audio/x-wav', 'size': 4},
                    {'ID': '34567', 'objid': 'bar', 'fname': '34567.pdf', 'mimetype': 'application/pdf', 'size': 6},
                ]}
            )

    def cmd_raise(self, args):
        raise ValueError()  # pragma: no cover

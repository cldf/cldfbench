from cldfbench import Dataset, CLDFSpec


class Thing(Dataset):
    id = 'thing'

    def cldf_specs(self):  # pragma: no cover
        return {
            None: Dataset.cldf_specs(self),  # The default spec
            'structure': CLDFSpec(dir=self.cldf_dir, module='StructureDataset'),
        }

    def cmd_makecldf(self, args):  # pragma: no cover
        with self.cldf_writer(args) as w:
            w.cldf.add_component('ValueTable')
            w.cldf.add_component('LanguageTable')
            w.objects['LanguageTable'].append({'ID': 'l1', 'Glottocode': None})
            w.objects['LanguageTable'].append({'ID': 'l2', 'Glottocode': 'xxxx9999'})
            w.objects['LanguageTable'].append({'ID': 'l3', 'Glottocode': 'book1111'})
            w.objects['ValueTable'].append(
                {'ID': 1, 'Language_ID': 'l1', 'Parameter_ID': 'p', 'Value': 'v'})
            w.objects['ValueTable'].append(
                {'ID': 1, 'Language_ID': 'l3', 'Parameter_ID': 'p', 'Value': 'v'})

        with self.cldf_writer(args, cldf_spec='structure', clean=False):
            w.objects['ValueTable'].append(
                {'ID': 1, 'Language_ID': 'l1', 'Parameter_ID': 'p', 'Value': 'v'})

    def cmd_raise(self, args):
        raise ValueError()  # pragma: no cover

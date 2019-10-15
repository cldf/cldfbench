from cldfbench.dataset import Dataset


class Thing(Dataset):
    id = 'thing'

    def cmd_makecldf(self, args):  # pragma: no cover
        with self.cldf_writer(args) as w:
            w.cldf.add_component('ValueTable')
            w.cldf.add_component('LanguageTable')
            w.objects['LanguageTable'].append({'ID': 'l1', 'Glottocode': None})
            w.objects['LanguageTable'].append({'ID': 'l2', 'Glottocode': 'xxxx9999'})
            w.objects['ValueTable'].append(
                {'ID': 1, 'Language_ID': 'l1', 'Parameter_ID': 'p', 'Value': 'v'})

    def cmd_raise(self, args):
        raise ValueError()  # pragma: no cover

# `cldfbench` Tutorial

In this tutorial we use `cldfbench` to create a CLDF `StructureDataset` from
the data of the [WALS](https://wals.info) feature ["Consonant Inventories"](https://wals.info/feature/1A).

1. Create a dataset directory, initialized with a skeleton suitable for 
   curation with `cldfbench`:

   ```bash
   $ cldfbench new
   id: theid
   title: The Title 
   license: CC-BY
   url: 
   citation: 
   ```
   Note that we specified `theid` as dataset ID when prompted. So now we should see
   a directory `theid` in our working directory:

   ```bash
   $ tree theid/
   theid/
   ├── cldf
   │   └── README.md
   ├── cldfbench_theid.py
   ├── etc
   │   └── README.md
   ├── metadata.json
   ├── raw
   │   └── README.md
   ├── setup.cfg
   ├── setup.py
   └── test.py
   ```

2. Now edit the python module `theid/cldfbench_theid.py`, filling in functionality
   to download the "raw" data from WALS. A `cldfbench.Dataset` provides several
   convenience methods for this kind of task. So in our case, it's a one-liner:
   ```python
       def cmd_download(self, **kw):
           self.raw_dir.download('https://wals.info/feature/1A.tab', '1A.tsv')
   ```
   Having implemented the command, we can run it from the command line:
   ```bash
   $ cldfbench download theid/cldfbench_theid.py 
   INFO    running cmd_download on theid ...
   INFO    ... done theid [0.5 secs]
   ```
   And inspect whether it did the right thing:
   ```bash
   $ tree theid/raw/
   theid/raw/
   ├── 1A.tsv
   └── README.md
   ```

3. Now we want to convert WALS' quirky `tab` format to nice CLDF. We do so by
   implementing the `cmd_makecldf` method:
   ```python
   def cmd_makecldf(self, **kw):
       with self.cldf_writer(cldf_spec=CLDFSpec(module='StructureDataset')) as ds:
           for row in self.raw_dir.read_csv(
                   '1A.tsv',
                   dicts=True, 
                   dialect=Dialect(
                       skipRows=5,  # Ignore the citation info on top
                       skipBlankRows=True,
                       delimiter='\t',
                   )
           ):
               ds.objects['ValueTable'].append({
                   'ID': row['wals code'],
                   'Language_ID': row['wals code'],
                   'Parameter_ID': '1A',
                   'Value': row['description'],
               })
   ```
   Let's break this down:
   - `with self.cldf_writer(...) as ds:` initializes a `cldfbench.cldf.CLDFWriter`
     (and implicitly a `pycldf.Dataset`), making sure the CLDF data will be written
     to disk after leaving the `ẁith` context.
   - The `cldfbench.cldf.CLDFSpec` instructs the writer to use the `StructureDataset` module.
   - Then we iterate over the rows of the downloaded data. Again, `cldfbench`
     provides convenient access to a `csvw.dsv.reader`, which understands multiple
     CSV dialects. We specify a dialect that can cope with WALS' format, ignoring
     the citation info at the top, and splitting columns on `\t`.
   - For each row in the input data, we append a row to the `StructureDataset`'s
     `ValueTable`.

   Again, we can run the command from the command line:
   ```bash
   $ cldfbench makecldf theid/cldfbench_theid.py ../glottolog/glottolog
   INFO    running cmd_makecldf on theid ...
   INFO    ... done theid [0.1 secs]
   ```
   Note that we had to pass an additional argument: The path to a clone of the
   [glottolog/glottolog](https://github.com/glottolog/glottolog) repository,
   because CLDF datasets should link to standard reference catalogs.

   Inspecting the results, we see ...
   ```bash
   $ tree theid/cldf
   theid/cldf
   ├── README.md
   ├── StructureDataset-metadata.json
   └── values.csv
   ```
   ... a valid CLDF dataset:
   ```bash
   $ cldf stats theid/cldf/StructureDataset-metadata.json 
   <cldf:v1.0:StructureDataset at theid/cldf>
   key            value
   -------------  ----------------------------------------------------
   dc:conformsTo  http://cldf.clld.org/v1.0/terms.rdf#StructureDataset
   rdf:type       http://www.w3.org/ns/dcat#Distribution

   Path        Type          Rows
   ----------  ----------  ------
   values.csv  ValueTable     563
   ```


## Going further

TODO
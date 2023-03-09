# `cldfbench` Tutorial

In this tutorial we use `cldfbench` to create a CLDF `StructureDataset` from
the data of the [WALS](https://wals.info) feature ["Consonant Inventories"](https://wals.info/feature/1A).

Throughout the tutorial we will interact with `cldfbench`'s **c**ommand **l**ine **i**nterface.
This cli is a single command `cldfbench`, providing access to subcommands. To get a list of available
subcommands, run
```shell script
cldfbench -h
```
to get help on usage of a particular subcommand (e.g. the subcommand `new`), run
```shell script
cldfbench new -h
```

1. Create a dataset directory, initialized with a skeleton suitable for 
   curation with `cldfbench`:

   ```shell script
   $ cldfbench new
   id: theid
   title: The Title 
   license: CC-BY
   url: 
   citation: 
   ```
   Note that we specified `theid` as dataset ID when prompted. So now we should see
   a directory `theid` in our working directory:

   ```shell script
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
       def cmd_download(self, args):
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
   implementing the `cldf_specs` method, to specify that we want to create a `StructureDataset` (note that this should replace the already existing definition of `cldf_specs` in the `Dataset` class):
   ```python
   def cldf_specs(self):
       from cldfbench import CLDFSpec
       return CLDFSpec(dir=self.cldf_dir, module='StructureDataset') 
   ```
   and implementing the `cmd_makecldf` method:
   ```python
   def cmd_makecldf(self, args):
       from csvw.dsv_dialects import Dialect
       for row in self.raw_dir.read_csv(
           '1A.tsv',
           dicts=True, 
           dialect=Dialect(
               skipRows=5,  # Ignore the citation info on top
               skipBlankRows=True,
               delimiter='\t',
           )
       ):
           args.writer.objects['ValueTable'].append({
               'ID': row['wals code'],
               'Language_ID': row['wals code'],
               'Parameter_ID': '1A',
               'Value': row['description'],
           })
   ```
   Let's break this down:
   - Then we iterate over the rows of the downloaded data. Again, `cldfbench`
     provides convenient access to a `csvw.dsv.reader`, which understands multiple
     CSV dialects. We specify a dialect that can cope with WALS' format, ignoring
     the citation info at the top, and splitting columns on `\t`.
   - For each row in the input data, we append a row to the `StructureDataset`'s
     `ValueTable`.
   - Because we only create a single CLDF dataset here, we do not need to call
     `with self.cldf_writer(...) as ds:` explicitly. Instead, an initialized
     `cldfbench.cldf.CLDFWriter` instance is available as `args.writer`.

   Again, we can run the command from the command line:
   ```shell script
   $ cd theid
   $ cldfbench makecldf cldfbench_theid.py --glottolog ../glottolog/glottolog
   INFO    running cmd_makecldf on theid ...
   INFO    ... done theid [0.1 secs]
   ```
   Note that we had to pass an additional argument: The path to a clone of the
   [glottolog/glottolog](https://github.com/glottolog/glottolog) repository,
   because CLDF datasets should link to standard reference catalogs.

   Inspecting the results, we see ...
   ```shell script
   $ tree theid/cldf
   theid/cldf
   ├── README.md
   ├── StructureDataset-metadata.json
   └── values.csv
   ```
   ... a valid CLDF dataset:
   ```shell script
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

The CLDF data we have created so far was pretty bare-bones. We should at least include
some metadata about the languages, and ideally also some information about the feature
(or parameter in CLDF lingo), e.g. a description of the values for the
[categorical variable](https://en.wikipedia.org/wiki/Categorical_variable) used in this
example.

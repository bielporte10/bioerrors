# BioErrors

A catalogue of bioinformatics failures traced to their real cause.

**Live: https://bielporte10.github.io/bioerrors/**

Paste an error, a log excerpt or a stack trace, and it tells you what actually
broke and what to do next — for Nextflow, Snakemake, conda, Docker, samtools,
GATK, R, Java tools and HPC schedulers.

## How it works

There is no server, no API key and no account. The catalogue lives in the
page's own JavaScript, so matching happens entirely in your browser and
nothing you paste is uploaded anywhere.

## Why it exists

Searching a bioinformatics error usually lands you on a forum thread from
several years ago where the answer is buried in a comment, or a general
chatbot that infers something plausible from the error text alone.

Every entry here is either documented behaviour of the tool itself, or was
traced from a real question by reading the source, the config file or the log
the tool actually wrote. Entries marked *traced* say where they came from —
for example, the `$BWA` entry comes from reading AMR++'s `params.config` and
`bwa.nf`, and the `.vmoptions` entry from Cytoscape's own launch docs.

The catalogue only answers what it knows. When it doesn't recognise an error
it says so plainly rather than guessing — that honesty is the point.

## Contributing an error

If it doesn't recognise your error, that is the useful case. Open an issue
with the error text and what you were running, and it gets traced and added.

## Licence

MIT.

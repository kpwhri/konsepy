# Changelog

All notable changes to this project should be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Reference

Types of changes:

* `Added`: for new features.
* `Changed`: for changes in existing functionality.
* `Deprecated`: for soon-to-be removed features.
* `Removed`: for now removed features.
* `Fixed`: for any bug fixes.
* `Security`: in case of vulnerabilities.

## [Unreleased]

### Added

* Added `--metadata-labels` to be able to supply metadata to the run function. Uses
  `--metadata-labels source_col==dest_variable[==type[==format]]`.
* Added organisation to requirements/pyproject files.

### Changed

* Inject `clean_args` function to 'fix' the rather generous `--metadata-labels`.

## [0.0.15] - 2024-09-26

### Fixed

* Speed up processing by not re-running function on text when no concepts were found (empty list is False)
* Fixed issues around Enums being output as the variables in generated CSV files.

## [0.0.14] - 2024-09-25

### Added

* Added check/warning if `include_match` not present on `RUN_REGEXES_FUNC`

### Changed

* Instead of dumping text into run_all's output jsonl, just output matches

### Fixed

* Skip call to `random` if probability is 1.0
* Warn when `input_file` is not read
* Don't dump all the input text to jsonl outfile when running

## [0.0.13] - 2024-08-30

### Fixed

* Added `kwargs` to handle otherwise unknown keyword arguments.
* Added warning when an input corpus file is not read (previously, this would cause an obscure error)

## [0.0.12] - 2024-04-12

### Added

* Script to convert any input corpus to jsonl files formatted for use by prodigy
    * jsonl files can be split by sentence/sentence chunks/moving window of sentences
* Add encoding argument for reading corpus (defaults to `latin1` as before)
* Convert jsonl file to `datasets.DatasetDict` for processing with `transformers` library
* Function to train a model on the `datasets.DatasetDict` using a pretrained model
* Log progress when running `get_text_snippets` every 1000 records
* Expand bio_tag to process at document level, sentence level, and/or jsonl corpus

### Changed

* `get_text_snippets` when applied to existing concepts will default to use the `RUN_REGEX_FUNC` unless the
  `--no-regex-func` flag is supplied

## [0.0.11] - 2023-11-16

### Added

* Read `jsonl` corpus
* Add incremental output (especially for memory-constrained environments/large corpora) with option to turn off
  collection of aggregate data.
* Search regexes and apply a function on the match to determine result category.

### Fixed

* Fixed logic for getting text snippets for concepts so that specifying no concepts results in getting all concepts.

## [0.0.10] - 2023-06-26

### Fixed

* Created sas7bdat file for testing and fixed a number of issues in the SAS pipeline

## [0.0.9] - 2023-06-23

### Fixed

* When checking SAS columns, check for its presence in the header rather than if it is None since it has a default value

## [0.0.7] & [0.0.8] - 2023-06-13

### Fixed

* Fixed where `noteorder_label` didn't yet get correctly passed around
* `enum.EnumType` is only available in 3.11+, so reverted to old `enum.EnumMeta`

## [0.0.6] - 2023-05-04

### Added

* Added `noteorder_label` to allow notes to appear in a delined form (with multiple rows for a note)
* Powershell script to test konsepy_nlp_template tutorial

## [0.0.5] - 2023-04-17

### Fixed

* Argument descriptions for column labels

[unreleased]: https://github.com/kpwhri/konsepy/compare/0.1.0...HEAD

[0.1.0]: https://github.com/kpwhri/konsepy/compare/0.0.15...0.1.0

[0.0.15]: https://github.com/kpwhri/konsepy/compare/0.0.14...0.0.15

[0.0.14]: https://github.com/kpwhri/konsepy/compare/0.0.13...0.0.14

[0.0.13]: https://github.com/kpwhri/konsepy/compare/0.0.12...0.0.13

[0.0.12]: https://github.com/kpwhri/konsepy/compare/0.0.11...0.0.12

[0.0.11]: https://github.com/kpwhri/konsepy/compare/0.0.10...0.0.11

[0.0.10]: https://github.com/kpwhri/konsepy/compare/0.0.9...0.0.10

[0.0.9]: https://github.com/kpwhri/konsepy/compare/0.0.8...0.0.9

[0.0.8]: https://github.com/kpwhri/konsepy/compare/0.0.7...0.0.8

[0.0.7]: https://github.com/kpwhri/konsepy/compare/0.0.6...0.0.7

[0.0.6]: https://github.com/kpwhri/konsepy/compare/0.0.5...0.0.6

[0.0.5]: https://github.com/kpwhri/konsepy/releases/0.0.5
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

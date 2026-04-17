News
=====

0.2.12
-------------------
General
+++++++++++++

* **Curated Bibliographic Overhaul**: Comprehensive metadata synchronization across 10 standards (Zenodo, CFF, CodeMeta, etc.) for FAIR compliance.
* **Online Repository Integration**: Formal links established between core software, analysis scripts, and the master Open Research Collection.
* **Technological Readiness**: Patched core modules for NumPy 2.0 and Pandas compatibility.

0.2.8
-------------------
New Features
+++++++++++++

* New feature `events_find()`: is now able to combine multiple digital input channels,
  retrieve events from the combined events channel and differentiate between the inputs that
  occur simultaneously.

0.2.4
-------------------
Fixes
+++++++++++++

* `eda_sympathetic()` has been reviewed: low-pass filter and resampling have been added to be in
  line with the original paper
* `eda_findpeaks()` using methods proposed in nabian2018 is reviewed and improved. Differentiation
  has been added before smoothing. Skin conductance response criteria have been revised based on
  the original paper.


SB-AKE research reproducibility package (24 September 2026)
==========================================================

CONTENTS
--------
1. sbake_reproducibility.py -- complete, executable Monte-Carlo simulation.
2. SB_AKE_repro_outputs/ -- input manifest, 10,000-trial results for both
   profiles at N={1,2,3,5,10}, gamma robustness, broad analytical
   sensitivity (1-1000 ms/slice), figures, and CSV data.
3. baseline_ProVerif/ -- archived earlier core-AKE model and its README.
   This source does NOT prove the full PUF->ML-DSA / dual-ML-KEM / multi-slice
   construction, and was not newly executed as part of this revision.
4. SB_AKE_equations_plain_text.txt -- alternate text transcription of the 42
   displayed native Word equations for readers with limited OMML support.
5. REVIEWER_RESPONSE_SUMMARY.txt -- changes and outstanding validation gates.
6. SHA256SUMS.txt -- SHA-256 checksums of the payload contents.

RUN THE SIMULATION
------------------
Python 3.10+ recommended. Install dependencies:

    python -m pip install numpy pandas matplotlib

Run from the directory containing sbake_reproducibility.py:

    python sbake_reproducibility.py

Results are written to ./SB_AKE_repro_outputs/ with fixed seed 20260924.
Each profile x slice count uses 10,000 draws in the primary run. Gamma
robustness reuses a separately seeded 10,000-draw run per configuration.
The analytical wide sensitivity is NOT Monte-Carlo data.

Provenance: Karcz et al., PLOS ONE 21(8), e0355179, 2026,
https://doi.org/10.1371/journal.pone.0355179 , Tables 5, 7 and 8,
workload + BLE + Wi-Fi scenario.

Six marginal per-operation means and standard deviations from the publication
were transcribed in the script. Raw joint traces were unavailable; the
assumption of independent primitive draws is a modeled approximation.
Positive lognormal and moment-matched gamma draws are simulation choices;
the study DID NOT measure our complete SB-AKE protocol.

The baseline uses one endpoint ML-DSA identity key generation per
multi-slice authorization event and a separate authenticated-PQ exchange
for each slice. The shared per-slice setup term (10 +/- 1 ms) represents
abstract context-derived state installation, including a KDF; it is NOT
measured in the source. A zero-setup independent-baseline stress test and
wide 1-1000 ms per-slice sensitivity are included.

LIMITATIONS
-----------
No present-study physical ESP32-C6, SRAM-PUF reliability/entropy, board energy,
integrated memory or radio/network measurements are reported. The complete
Section 4 protocol still requires full-ProVerif experiments, and a physically
instantiated PUF needs an early boot acquisition feasibility gate. These are
explicit remaining prerequisites for venues requiring full security/embedded
validation.

Baseline ProVerif (OPTIONAL): install ProVerif separately and run:

    proverif baseline_ProVerif/SB_PAKE_ProVerif_Model.pv

Only attribute the baseline verified claims to the exact archived model;
verify tool version and archive the raw ProVerif log separately. This package
does not claim to provide newly executed full-protocol symbolic results.

ARTIFACT AVAILABILITY
---------------------
A permanent DOI or repository URL has not yet been assigned. If submitting
to a journal requiring public, persistent reproducibility artifacts, archive
this package in an appropriate repository and add the real accession URL to
the manuscript. Do not cite a nonexistent repository or claim hardware tests.

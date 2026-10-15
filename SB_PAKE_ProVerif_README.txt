SB-PAKE ProVerif Verification Instructions
==========================================

Files:
- SB_PAKE_ProVerif_Model.pv

How to run:
1. Install ProVerif from the official ProVerif distribution.
2. Open a terminal in the folder containing SB_PAKE_ProVerif_Model.pv.
3. Run:

   proverif SB_PAKE_ProVerif_Model.pv > SB_PAKE_ProVerif_Result.txt

Expected successful results should include results equivalent to:

1. RESULT not attacker(testsecret[]) is true.
   Meaning: application data encrypted under an accepted SB-PAKE session key remains secret.

2. RESULT inj-event(endSF(...)) ==> inj-event(beginE(...)) is true.
   Meaning: if the slice-serving function accepts, then a matching endpoint run occurred with the same ID_i, S-NSSAI, Role_i, Policy_i, ep, nonces, and session key.

3. RESULT inj-event(endE(...)) ==> inj-event(beginSF(...)) is true.
   Meaning: if the endpoint accepts, then a matching slice-serving-function run occurred with the same slice-bound context and session key.

Important limitation:
This ProVerif model abstracts ML-KEM as a secure KEM and abstracts the SRAM-PUF/fuzzy extractor as a private reconstructed endpoint key K_i. Therefore, the model verifies symbolic Dolev-Yao message-flow properties, not the computational hardness of ML-KEM and not the entropy/reliability of a physical SRAM-PUF.

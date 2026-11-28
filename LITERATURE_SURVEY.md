# PawFect — Literature Survey
### AI Pet-Adoption Matchmaker (Android + FastAPI + LLM + Vector Search)
**Course:** Mobile App Development — College Project  
**Scope:** Pet-adopter compatibility science + technology used to execute the idea  
**Included:** 15 papers (2019–2026) | **Excluded:** listed with rationale in §4

---

## 1. Project in one paragraph

PawFect is an Android (Jetpack Compose) app with a FastAPI backend that (1) interviews adopters with an LLM counselor, (2) builds structured lifestyle constraints (species, housing, energy, kids/pets, allergies, experience, time-at-home), (3) rule-filters + vector-searches shelter pets in MongoDB Atlas, (4) reranks / explains compatibility with an LLM, and (5) guides the adoption application. This survey grounds each of those choices in prior work.

**Inclusion criteria:** peer-reviewed or widely-cited preprint, 2018–2026, directly maps to a PawFect subsystem, actionable finding or architecture pattern. **Exclusion:** pre-2018 superseded work, pure-pretraining papers with no retrieval/recommendation content, methods needing training data we do not have (collaborative filtering, KG training).

---

## 2. Included papers (15)

### CLUSTER A — Pet-adopter compatibility (why matches fail, what predicts fit)

#### A1. Dolan et al. 2021 — Characterizing unsuccessful animal adoptions
- **Full citation:** Dolan, E. D., Wills, A. P., & Dean, R. S. (2021). Characterizing unsuccessful animal adoptions: age and breed predict the likelihood of return, reasons for return and post-return outcomes. *Scientific Reports*, 11, 8018. https://doi.org/10.1038/s41598-021-87649-2
- **Research question:** Which animal-level factors predict return?
- **Method:** Retrospective cohort, 23,932 adoptions (2015–2019), logistic regression.
- **Key finding:** 9.2% returned in 6 months (dogs 16.3%, cats 4.2%). Top dog reason: behavioral issues (36.1%). Top cat reason: incompatibility with existing pets (22.0%). Adult dogs OR 3.40 vs puppies; senior cats OR 4.97 vs kittens.
- **Shortcoming:** Owner self-reported reasons (κ = 0.08 between first/second return), single shelter, no adopter-lifestyle data.
- **What PawFect does:** Encodes these as screening constraints — existing-pets question, energy-level match, household composition, age-risk flag in compatibility scoring. Turns population risk into per-adopter screening.

#### A2. Dolan et al. 2022 — Impact of returning a pet on future adoptions
- **Full citation:** Dolan, E. D., Weiss, E., & Dean, R. S. (2022). The impact of returning a pet to the shelter on future animal adoptions. *Scientific Reports*, 12, 1796. https://doi.org/10.1038/s41598-022-05101-5
- **Research question:** Do returners adopt again, and what predicts it?
- **Method:** Logistic regression on 1,999 return events.
- **Key finding:** Only 10.5% adopted again within 12 months. Unrealistic expectations OR 0.42 for re-adoption. Behavioral returns least likely to try again.
- **Shortcoming:** Single shelter, retrospective, misses adopters who go elsewhere.
- **What PawFect does:** Interview asks usage questions (“how many hours home daily?”) instead of attribute questions to surface unrealistic expectations early; weights behavioral compatibility highest in the LLM rubric.

#### A3. Curb et al. 2022 — Selection factors and owner satisfaction
- **Full citation:** Curb, L. A., Abramson, C. I., Grice, J. W., & Kennison, S. M. (2022). Selection factors influencing eventual owner satisfaction about pet dog adoption. *Animals*, 12(17), 2264. https://doi.org/10.3390/ani12172264
- **Research question:** Which selection factors predict satisfaction?
- **Method:** Survey of 933 adopters, ordinal logistic regression.
- **Key finding:** Prioritizing personality over appearance raises satisfaction; companionship motivation beats exercise-partner / family-request motivations.
- **Shortcoming:** 92% female, self-selected, cross-sectional, no longitudinal follow-up.
- **What PawFect does:** Elicits motivation first, soft-warns on family-request / exercise-partner motives, shows behavioral descriptors before photos, weights personality/energy above breed/appearance in scoring.

#### A4. Mariti et al. 2022 — Assessing behavioral compatibility (C-BARQ)
- **Full citation:** Mariti, C., Mazzoni, C., & Gazzano, A. (2022). Assessing behavioral compatibility between shelter dogs and potential adopters. *Agricultura*, 19(1–2), 63–70. https://journals.usamvcluj.ro/index.php/agricultura/article/view/15173
- **Research question:** Can C-BARQ dog profiles + adopter profiles predict compatible matches?
- **Method:** C-BARQ on 49 shelter dogs + 78 adopter questionnaires, compatibility cross-tabs.
- **Key finding:** Active adopters ↔ excitable dogs; calm homes ↔ anxious dogs. Standardized assessment beats in-shelter observation.
- **Shortcoming:** Small sample, needs expert raters + staff time, no post-adoption tracking.
- **What PawFect does:** Digitizes the idea — behavioral tags (excitability, fearfulness, aggression history) become structured + vector-searchable pet fields entered at intake; LLM reasons over them vs adopter activity/home automatically. Solves the scalability bottleneck.

#### A5. Zhu et al. 2020 — Predicting length of stay + shelter allocation
- **Full citation:** Zhu, C., et al. (2020). Increasing adoption rates at animal shelters: a two-phase approach to predict length of stay and optimal shelter allocation. *BMC Veterinary Research*, 16, 404. https://doi.org/10.1186/s12917-020-02728-2
- **Research question:** Can ML predict length-of-stay and optimize relocation?
- **Method:** LogReg, ANN, gradient boosting (best), random forest + goal programming.
- **Key finding:** Gradient boosting best; age/size/coat predict stay; no behavioral features — flagged as critical gap.
- **Shortcoming:** No behavioral data, operations KPI (stay length) not adoption success, hard for understaffed shelters to deploy.
- **What PawFect does:** Adds the missing behavioral layer to the pet schema so similarity search uses more than demographics; rule-filter before vector search; future work: FastAPI endpoint flagging long-stay animals for proactive matching.

#### A6. Torres et al. 2024 — PAWrfect Match (baseline we supersede)
- **Full citation:** Torres, L. J. F., de Leon, C. J. S., Callado, F. A. D., Cuartero, J. D. Z., Centeno, C. J., & Casiw, G. M. (2024). PAWrfect Match: A Web-Based Animal Adoption and Rescue System that uses Content-Based Filtering Algorithm for Recommending Potential Adoptees. *Library Progress International*. https://bpasjournals.com/library-science/index.php/journal/article/view/3971
- **Research question:** Can a web system advertise shelter pets + content-filter recommendations from a sign-up pre-survey?
- **Method:** Built system: static pre-survey → content-based filtering + notifications + rescue requests + forum.
- **Key finding:** Works as advertising platform; static survey → keyword match is sufficient for browsing.
- **Shortcoming:** Static checkboxes cannot capture context (“toddler afraid of large dogs but near park”), cannot update mid-dialogue, no multi-dimensional reasoning, no explanation.
- **What PawFect does:** Replaces static survey with conversational LLM interview → structured constraints → vector + LLM rerank + natural-language why-it-fits explanation. Same problem, strictly more expressive input and output.

---

### CLUSTER B — Conversational + retrieval technology

#### B1. Lewis et al. 2020 — Retrieval-Augmented Generation (RAG)
- **Full citation:** Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS* 33, 9459–9474. https://arxiv.org/abs/2005.11401
- **RQ / Method:** Combine dense retriever (non-parametric memory) + seq2seq (parametric) over Wikipedia; test on NQ/TriviaQA/WebQuestions/FEVER.
- **Finding:** SOTA on 3 QA tasks; more factual/specific; knowledge updatable without retraining.
- **Shortcoming:** Static encyclopedic corpus, no dynamic structured-DB or latency analysis.
- **What PawFect does:** Swaps Wikipedia for Atlas Vector Search over pet profiles (updated on intake/adoption, no retraining). LLM = reasoning, index = memory.

#### B2. Karpukhin et al. 2020 — Dense Passage Retrieval (DPR)
- **Full citation:** Karpukhin, V., et al. (2020). Dense passage retrieval for open-domain question answering. *EMNLP*, 6769–6781. https://arxiv.org/abs/2004.04906
- **RQ / Method:** Dual BERT encoders + dot-product + in-batch negatives + FAISS.
- **Finding:** +9–19% absolute top-20 over BM25.
- **Shortcoming:** Needs in-domain fine-tuning; ANN recall tradeoff at scale.
- **What PawFect does:** Adopter-constraint vector = query encoder, pet embedding = passage encoder, HNSW in Atlas. Corpus is hundreds–thousands so exact search is feasible — avoids the large-scale recall penalty.

#### B3. Reimers & Gurevych 2019 — Sentence-BERT
- **Full citation:** Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. *EMNLP-IJCNLP*, 3982–3992. https://arxiv.org/abs/1908.10084
- **RQ / Method:** Siamese/triplet BERT on SNLI/MultiNLI; pooling compared.
- **Finding:** 10k-pair comparison 65 hrs → ~5 sec at BERT-level accuracy; +11.7 over InferSent on STS.
- **Shortcoming:** Small accuracy loss vs cross-encoder; symmetric network weak for asymmetric query-doc.
- **What PawFect does:** Uses SBERT-class bi-encoders for pet + adopter profiles for millisecond cosine retrieval; reserves accuracy step for cross-encoder/LLM rerank on top-K only.

#### B4. Nogueira & Cho 2019 — Passage re-ranking with BERT
- **Full citation:** Nogueira, R., & Cho, K. (2019). Passage re-ranking with BERT. *arXiv:1901.04085*. https://arxiv.org/abs/1901.04085
- **RQ / Method:** BERT-Large cross-encoder binary classifier reranking BM25 top-1000 on MS MARCO.
- **Finding:** +27% relative MRR@10, SOTA with <0.3% training data. Established retrieve→rerank pattern.
- **Shortcoming:** O(K) cost, cannot precompute, infeasible for K>1000 latency.
- **What PawFect does:** Reranks only K=20–50 from vector search, so O(K) is mobile-tolerable. LLM evaluator acts as “super cross-encoder” that scores + explains.

#### B5. Deng et al. 2023 — RecLLM (LLM conversational recommender)
- **Full citation:** Deng, S., et al. (2023). Leveraging large language models in conversational recommender systems. *arXiv:2305.07961*. https://arxiv.org/abs/2305.07961
- **RQ / Method:** Proof-of-concept on LaMDA/YouTube: unified LLM for dialogue + NL user profile + retrieve-then-LLM-rank with joint score + explanation.
- **Finding:** One LLM can replace policy graphs; NL profiles > opaque embeddings for transparency; LLM rankers explain via chain-of-thought.
- **Shortcoming:** Illustrative only, no quantitative eval; hallucination unsolved; no mobile/latency/cold-start treatment.
- **What PawFect does:** Same blueprint (counselor + FastAPI retrieval + LLM ranker) but grounds outputs in retrieved pet records (RAG) + strict JSON constraint schema so the model never invents pet IDs. Adds cold-start interview as the default path.

#### B6. ICLR 2026 — Interactive preference elicitation in latent space
- **Full citation:** Supporting high-stakes decision making through interactive preference elicitation in the latent space. *ICLR 2026*. https://proceedings.iclr.cc/paper_files/paper/2026/file/5a161a9070cb7b259abe84cb37ed1b6f-Paper-Conference.pdf
- **RQ / Method:** Preferential Bayesian optimization in autoencoder latent space + LLM cold-start interview → probabilistic prior; tested on Idealista18 + Munich rentals; pairwise ranking accuracy.
- **Finding:** Latent-space PBO +12%; probabilistic LLM priors +25% over static prior.
- **Shortcoming:** Real-estate only, pairwise-comparison fatigue, AE may not transfer to categorical behavioral features.
- **What PawFect does:** Same interview→prior→retrieve→rerank shape, but fixed-round interview (less fatigue) + vector + cross-encoder (better for small fast-changing shelter inventories). Uses LLM to infer constraint confidences, not ask users for weights.

#### B7. Lim et al. 2024 — SuDoSys structured counseling dialogue
- **Full citation:** Lim, J., et al. Structured dialogue system for mental health: an LLM chatbot leveraging the PM+ guidelines. *arXiv:2411.10681*. https://arxiv.org/html/2411.10681v1
- **RQ / Method:** Stage controller → instruction generator → LLM → response unpacker → topic DB; PM+ transcripts + 20-student study.
- **Finding:** Highest coherence/authenticity without fine-tuning; unpacker repairs malformed JSON.
- **Shortcoming:** Chinese PM+ therapy domain, GPT-judge bias, n=20.
- **What PawFect does:** Copies the pattern: staged adoption arc (lifestyle → housing → energy → pets/kids → allergies → experience) with a controller deciding when to switch from gathering to retrieval; backend parses/repairs constraint JSON instead of trusting raw LLM output. No fine-tuning needed — fits college compute budget.

---

### CLUSTER C — Mobile execution (why cloud, how Android talks to FastAPI)

#### C1. Lin et al. 2024 — LLM efficiency on mobile devices
- **Full citation:** Lin, Y., et al. (2024). Are we there yet? A measurement study of efficiency for LLM applications on mobile devices. *arXiv:2504.00002*. https://arxiv.org/html/2504.00002v1
- **RQ / Method:** Pixel 8 (8 GB) vs cloud vs edge: Llama-3.2 sizes, latency/tokens/mem/quality.
- **Finding:** Only <4B fits; >30 s on-device vs <10 s cloud; OS eats 35–40% RAM; compressed mobile models often incoherent.
- **Shortcoming:** One high-end device; mid-range worse; hardware shifting fast.
- **What PawFect does:** Justifies cloud inference via FastAPI. Compose app sends utterances over Retrofit/OkHttp coroutines; backend calls LLM + retrieval and returns structured JSON. No on-device counselor.

#### C2. Bansal & Singla 2025 — FastAPI + Android integration
- **Full citation:** Bansal, N., & Singla, B. (2025). Integration of FastAPI-Based Machine Learning Model with Android Application for Real-Time Calories Burnt Prediction. *J Fore Res*, 6(1), 01–09. https://www.opastpublishers.com/open-access-articles/integration-of-fastapibased-machine-learning-model-with-android-application-for-realtime-calories-burnt-prediction-9224.html
- **RQ / Method:** RandomForest + FastAPI (Pydantic, async, Swagger) + Android Retrofit/Gson/coroutines; 10.0.2.2 emulator vs LAN IP for physical devices; 0.0.0.0 hosting.
- **Finding:** R² 0.998 demo; async FastAPI + type-safe Retrofit = clean reproducible pattern; centralized updates, lightweight client, cross-platform consistency.
- **Shortcoming:** Single-model demo, no LLM/SSE/vector-search, security/auth minimal.
- **What PawFect does:** Reuses the exact pattern (Pydantic ↔ Kotlin data classes, Retrofit suspend calls, 10.0.2.2/LAN-IP handling, 0.0.0.0 + reload) but upgrades payload to chat/SSE + vector retrieval + LLM scoring. Direct template for our `NetworkModule`, `PawFectApiService`, `PawFectSseClient`.

---

## 3. Coverage matrix (paper → PawFect subsystem → gap fixed)

| # | Paper | Subsystem | Shortcoming → PawFect fix |
|---|-------|-----------|---------------------------|
| A1 | Dolan 2021 | Rule filter, constraints | No adopter data → ask existing-pets/energy/household; age-risk flags |
| A2 | Dolan 2022 | Interview design | Unrealistic expectations unmeasured → usage-questions + expectation screen |
| A3 | Curb 2022 | Interview + match cards | Appearance-first UI → personality-first cards, motivation screen |
| A4 | Mariti 2022 | Pet schema | C-BARQ not scalable → digitized behavioral tags + LLM reasoning |
| A5 | Zhu 2020 | Rule filter, shelter API | No behavior, ops-only → behavior-enriched vectors; future long-stay endpoint |
| A6 | Torres 2024 | Baseline | Static survey → conversational constraints + explained matches |
| B1 | Lewis 2020 | RAG architecture | Static corpus → dynamic Atlas pet index, no retraining on inventory change |
| B2 | Karpukhin 2020 | Vector search | Needs tuning, ANN loss → small corpus, exact search feasible |
| B3 | Reimers 2019 | Embeddings | Cross-encoder too slow → bi-encoder retrieve then rerank top-K |
| B4 | Nogueira 2019 | Rerank | O(K) expensive → K=20–50, mobile-tolerable; LLM explains |
| B5 | Deng 2023 | Counselor + pipeline | Hallucination, no eval → RAG grounding + JSON schema |
| B6 | ICLR 2026 | Cold-start prior | Real-estate only, fatigue → fixed-round interview, shelter-adapted retrieval |
| B7 | Lim 2024 | Stage control | Therapy/Chinese only → adoption-stage controller + JSON unpacker |
| C1 | Lin 2024 | Cloud vs on-device | On-device infeasible → FastAPI cloud inference |
| C2 | Bansal 2025 | Android↔FastAPI | Toy model → same Retrofit/Pydantic pattern for chat/SSE/vectors |

---

## 4. Excluded work (considered, deliberately not in the 15)

| Category / Example | Why excluded |
|---|---|
| Pre-2018 welfare literature (early C-BARQ validation, Shore 2005 relinquishment) | Superseded by larger recent multi-shelter studies (A1–A3) |
| Pure pretraining (Devlin BERT 2018, GPT-3 2020) | Foundational but not actionable; covered via B2–B4 |
| Collaborative filtering / matrix factorization (Netflix-prize era) | Needs interaction history; PawFect is cold-start |
| Knowledge-graph recommenders (K-RagRec) | Marginal gain for structured shelter catalog; beyond college scope |
| ARAG multi-agent recommendation (2026) | 4-agent overhead; single-LLM counselor suffices; future work |
| CORAL contrastive CRS | Needs training data we lack; zero-shot LLM (B5) more practical |
| Zhao 2024 LightGBM pet-rescue prediction | Ops-level outcome prediction, incomplete dataset description; feature-importance idea already covered by A5 |
| Wang 2025 biomedical RAG benchmark | Useful cross-encoder evidence but biomedical QA does not transfer cleanly to semi-tabular pet profiles |
| Edge-AI surveys | Covered more directly by mobile measurement study C1 |
| Jetpack Compose vs XML comparative study | Validates Compose choice (less boilerplate, small perf delta) but is an implementation detail, not a research contribution; cited as supporting, not core |
| General CRS surveys | All actionable findings already in primary papers B5–B7 |

---

## 5. Gaps PawFect can claim as contribution

1. No paper combines conversational LLM elicitation with shelter behavioral data — PawFect is novel at this intersection.
2. Return studies lack adopter-lifestyle predictors — PawFect pilot data could enable that analysis.
3. C-BARQ has not been digitized into vector-searchable shelter DBs — PawFect schema does this.
4. ICLR-2026 high-stakes elicitation is real-estate only — PawFect extends it to adoption (categorical behavioral features).
5. No cross-encoder rerank evaluation for adoption — PawFect logs (view → apply → adopt) create that future dataset.

---

## References (the 15)

1. https://doi.org/10.1038/s41598-021-87649-2
2. https://doi.org/10.1038/s41598-022-05101-5
3. https://doi.org/10.3390/ani12172264
4. https://journals.usamvcluj.ro/index.php/agricultura/article/view/15173
5. https://doi.org/10.1186/s12917-020-02728-2
6. https://bpasjournals.com/library-science/index.php/journal/article/view/3971
7. https://arxiv.org/abs/2005.11401
8. https://arxiv.org/abs/2004.04906
9. https://arxiv.org/abs/1908.10084
10. https://arxiv.org/abs/1901.04085
11. https://arxiv.org/abs/2305.07961
12. https://proceedings.iclr.cc/paper_files/paper/2026/file/5a161a9070cb7b259abe84cb37ed1b6f-Paper-Conference.pdf
13. https://arxiv.org/html/2411.10681v1
14. https://arxiv.org/html/2504.00002v1
15. https://www.opastpublishers.com/open-access-articles/integration-of-fastapibased-machine-learning-model-with-android-application-for-realtime-calories-burnt-prediction-9224.html

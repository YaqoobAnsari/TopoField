# TopoField — Final Research Plan
## Hierarchical Topological Graph Representations of Institutional Buildings for Physical Field Inference

**Target venue:** CVPR 2026 (primary) · ICLR 2026 (alternate framing)
**Document status:** Finalized standalone research plan. Supersedes all prior planning documents.

---

# TABLE OF CONTENTS

1. Executive Summary and Claims
2. Research Gap Analysis (four independent audit lanes)
3. Literature Review
4. The HDG Representation — Formal Definition and Worked Example
5. Theoretical Grounding
6. Data Strategy and Annotation Budget
7. Phase-by-Phase Methodology
8. Model Architecture and Training Recipe
9. Dataset Inventory
10. Baseline Suite (full audit)
11. Metrics and Statistical Protocol
12. Hypotheses
13. Venue Fit Analysis
14. Risk Register
15. Timeline
16. Open Questions
17. Appendix A: Citation-Safety Table
18. Appendix B: Data Budget Worksheet

---

# 1. EXECUTIVE SUMMARY AND CLAIMS

**The problem.** Every published floorplan-understanding system is designed for and evaluated on residential-scale buildings (5–25 rooms). Institutional buildings — hospitals, campuses, large offices — contain 100+ heterogeneous rooms organized into functional hierarchies (departments, wards, fire compartments) with access-directed circulation. No existing representation captures this structure, no benchmark contains it, and no method has been tested against it.

**The three claims of this work:**

**C1 (Representation).** We introduce the Hierarchical Directed Graph (HDG): the first functional-hierarchical, access-directed, typed graph representation of buildings constructed from 2D architectural floorplans. It combines a containment hierarchy (room ⊂ corridor-cluster ⊂ zone ⊂ wing ⊂ building) with a cross-cutting typed physical-adjacency layer, including directed access-controlled edges.

**C2 (Downstream task family — headline).** We demonstrate that the HDG is a *backbone representation* for a family of spatial reasoning tasks beyond room identification, instantiated as three deliberately heterogeneous arms:

- **Task L — Indoor localization (external-benchmark anchor).** HDG-conditioned structural priors improve floorplan localization (FLoc) on *public* benchmarks (Structured3D, ZInD, Gibson-f) against published CVPR/ECCV baselines (F3Loc, LASER, LaLaLoc++). The literature already shows flat semantic cues (room labels) more than double F3Loc's recall; our hypothesis is that hierarchical functional structure — zone membership, corridor typing — extends this established trend, especially in large buildings with repetitive corridors, the canonical FLoc ambiguity case. Ground truth is real camera poses: no simulation, no circularity.
- **Task T — Thermal field inference (novel unclaimed task).** Does topology alone — no sensors at inference — predict thermal zoning and temperature ordering? Supervised by automated EnergyPlus simulation; the zero-sensor formulation is verified unclaimed (§2, Lane 2).
- **Task E — Egress/crowd flow (task-family demonstration).** Evacuation bottleneck ranking and relative egress-load prediction from topology, supervised by pedestrian/egress simulation (social-force or Pathfinder-class), sharing the Task-T labeling machinery. Anchored by the fact that corridor betweenness — computable from the HDG directly — is the zeroth-order theory of evacuation flow.

Rescue planning, crowd-control operations, and further applications are discussed as future work, not experimented — three deep arms beat five shallow ones.

**C3 (Benchmark).** We release InstBuild: the first benchmark of institutional-scale floorplans (30–50 buildings, 100+ rooms each) with verified HDG annotations and simulation-derived physical labels — a regime absent from every existing dataset (current maximum: 22 rooms/scene in Structured3D; multi-unit residential in MSD).

**What this work is deliberately NOT claiming.** We do not claim to be first to reconstruct complex floorplans (Raster2Seq, 2026, addresses geometric complexity at residential scale); we do not claim to have invented hierarchical building graphs with containment + peer edges (the 3D scene graph literature — Hydra, HOV-SG — has this pattern, from sensor streams); we do not claim novel graph-learning theory (we apply established hierarchy and directionality results). The novelty is the functional-institutional representation from drawings, the zero-sensor physical inference task, and the benchmark — each verified unclaimed in §2.

---

# 2. RESEARCH GAP ANALYSIS

Four independently scoped audit lanes were run against current literature (through mid-2026). Each lane reports what was found — including findings adverse to our claims — and the verdict.

## Lane 1 — Complexity-robust floorplan reconstruction

**Adverse finding.** Raster2Seq (Cornell, arXiv 2602.09016, Feb 2026) reconstructs floorplans as autoregressive labeled-polygon sequences with learnable spatial anchors. Because output is generated token-by-token, it has **no fixed room ceiling**. It explicitly motivates itself by failures of existing methods on "complex floorplans... with many rooms," and empirically documents that RoomFormer and FRI-Net degrade sharply past ~15 polygons / ~150 corners, including out-of-memory failures from quadratic attention. It achieves SOTA on Structured3D-B, CubiCasa5K, and Raster2Graph, and generalizes to WAFFLE.

**Boundary of the finding.** Raster2Seq's output is a flat sequence of independent polygons: no connectivity graph, no containment hierarchy, no typed or directed relations, no downstream inference. Its "complex" remains residential-benchmark complexity (~15–25 polygons), not institutional scale.

**Verdict.** A pure "first to handle scale" reconstruction claim is unavailable. Raster2Seq becomes our most important reconstruction baseline (§10), and the scale-cliff experiment is reframed: (a) does the newest ceiling-free architecture survive genuine institutional complexity? (b) even where its geometry holds, a polygon sequence scores nothing on structural-understanding metrics — quantifying the gap between reconstruction and understanding.

## Lane 2 — Physical field inference from building structure

**Finding.** The building-science ML literature (PINN thermal modeling; GNN-based HVAC model-predictive control incl. PhyGICS; LSTM/RNN multi-zone temperature prediction; ANN zone estimation for large venues) universally requires operational sensor time-series or calibrated simulation inputs at inference. The closest structural relatives use a building-structure graph only as a scaffold for propagating measured signals. No work in CV/ML or building science predicts thermal zoning, temperature ordering, or occupancy flow from floorplan-derived topology as the sole input.

**Verdict.** C2 is fully unclaimed. Differentiation sentence: existing thermal ML answers "what will this instrumented building do next?"; we ask "what can be known before any instrument is installed?"

## Lane 3 — Hierarchical building graphs

**Adverse finding.** Robotics has a mature hierarchical 3D scene graph (3DSG) line: 3DSG (ICCV 2019), Hydra (RSS 2022), S-Graphs+, HOV-SG (RSS 2024), HERO (2025), LLM-assisted 3DSGs (2025). These build layered graphs (mesh/places → objects → rooms → floors → building) whose edges include both hierarchical containment and peer-level relations (adjacency, traversability). The containment + peer-edge pattern is therefore established, not ours.

**Boundary.** All 3DSGs are constructed from RGB-D sensor streams and robot exploration — none from architectural drawings. Their hierarchies are geometric (floors, watershed room regions), never functional (departments, wards, compartments). Their accessibility edges are robot-traversability, not typed access control. Their purpose is navigation/language grounding, never physical inference. Their scale is apartments and small offices.

**Verdict.** C1 must be (and is) scoped as *functional* hierarchy from *drawings* at *institutional scale* for *physical inference*. The 3DSG line becomes mandatory related work, convergent design validation, and one ablation: geometric-only hierarchy (Hydra-style floors/rooms) vs our functional hierarchy (H4b, §12).

## Lane 4 — Floorplan-to-graph extraction (the construction problem)

**Finding.** Tesseract (Ansari, Karkour, Feo Flushing, Harras — CMU; SIGSPATIAL 2025, pp. 569–579, doi 10.1145/3748636.3762771) converts **low-semantic raster floorplans into navigable room-connectivity graphs**. Pipeline: resolution normalization + contrast enhancement → OCR/text-label handling (contrast tuning reduces fragmented text detections; bounding-box merges drop >80%) → segmentation → graph construction with corridor sampling. Evaluated on two real complex sites ("Site A," "Site B") plus SESYD, with per-module runtimes, linear scaling in floorplan complexity (number of text labels), navigational-completeness scores (proportion of pairwise room connections captured), and geometric fidelity (graph path distances vs pixel ground-truth distances between room centers). Supporting extraction literature: Raster-to-Graph (EG 2024; autoregressive wall-junction graphs, ~10K-plan dataset), Kim-Kim-Yu (ISPRS 2021; patch-based extraction explicitly for large-scale complex buildings, 87.8% detection / 85.5% recognition), Chen & Stouffs (2022; typed room-adjacency extraction: direct/door/window/wall).

**Boundary.** Tesseract outputs a flat navigable connectivity graph. It does not produce functional hierarchy, typed access direction, zone membership, or any learned representation; it is a geometric/heuristic pipeline for navigation use-cases, and its evaluation sites, while real and complex, are not released as a learning benchmark with physical labels.

**Verdict.** Tesseract is the **backbone of our Phase Zero raster lane** (it solves precisely the room-and-connectivity extraction step, with published evidence of linear scaling on label-dense complex plans) and additionally becomes a **baseline**: its heuristic navigable graph, fed to the same downstream heads, versus our HDG — isolating the value of functional hierarchy + typing + direction over a competent flat extraction (§10). It does not threaten C1–C3.

## Lane 5 — Floorplan localization (FLoc)

**Finding.** FLoc is an established vision task with public benchmarks and A*-venue baselines: LaLaLoc (ICCV 2021), LaLaLoc++ (ECCV 2022, global floorplan embedding), LASER (CVPR 2022, floorplan-as-point-set + PointNet pose features), and **F3Loc (CVPR 2024** — Chen, Wang, Vogel, Pollefeys): 1D floorplan-ray observation model + SE(2) histogram filtering, evaluated on Gibson(f) and Structured3D with recall@{0.1, 0.5, 1}m and @1m-30° metrics (e.g., 36.6% @1m on Gibson-f; 22.4% @1m on Structured3D). Active 2025–26 follow-ups (3DP, RSK, SPVLoc, UnLoc, DisCo-FLoc) confirm a living subfield. Most relevant: **Semantic Rays (2025)** shows that adding flat semantic cues (room-type labels) to ray-based matching *more than doubles* F3Loc's recall on Structured3D and ZInD.

**Boundary.** All existing FLoc methods condition on geometry (rays, points, layouts) or, at most, flat room-type semantics. None exploit structured functional priors — zone membership, corridor hierarchy, typed connectivity. And the canonical FLoc failure mode — ambiguity among repetitive, geometrically identical corridors — is exactly the structure institutional buildings maximize; no FLoc benchmark contains such buildings.

**Verdict.** A published, quantified trend line (semantics improve FLoc) points directly at our representation as its natural continuation; the structured-prior step is unclaimed. Task L therefore gives the project an arm evaluated on *external* benchmarks with *real* ground truth (camera poses) against *recognized* CVPR/ECCV baselines — repairing, in one move, the private-benchmark concentration and the simulation-circularity exposure of a thermal-only evaluation. Additionally, InstBuild's repetitive-corridor typology positions it as a future hard FLoc benchmark (noted as future work; InstBuild has no camera imagery, so Task L runs on public datasets whose HDGs we derive automatically from their vector ground truth).

## Consolidated gap statement

> Reconstruction research has begun addressing geometric complexity (Raster2Seq) at residential scale; robotics builds hierarchical scene graphs from sensor streams (Hydra, HOV-SG); GIS systems extract flat navigable graphs from drawings (Tesseract); floorplan localization exploits geometry and, at most, flat room-label semantics (F3Loc, Semantic Rays). No existing work (1) represents the functional hierarchy and directed access structure of institutional buildings from architectural drawings, (2) evaluates any method at genuine institutional scale (100+ heterogeneous rooms), (3) infers physical or operational field properties (thermal zoning, egress load) from building topology alone, or (4) conditions localization on structured functional priors. TopoField contributes all four, plus the first benchmark in this regime.

---

# 3. LITERATURE REVIEW

## 3.1 Floorplan reconstruction
Floor-SP (ICCV 2019): per-room shortest-path optimization; no ceiling but slow, Manhattan-biased. MonteFloor (ICCV 2021): MCTS over room proposals; "large-scale" in title, residential in evaluation; code unavailable. HEAT (CVPR 2022): corner detection → edge classification; two-stage error compounding on dense layouts. RoomFormer (CVPR 2023): two-level fixed queries; de-facto standard; documented degradation and OOM past ~15 polygons (per Raster2Seq). PolyRoom (ECCV 2024): Mask2Former-initialized queries; same ceiling; drops significantly off its home benchmark — published evidence of benchmark overfitting. FRI-Net (ECCV 2024): room-wise implicit fields; same complexity ceiling. SLIBO-Net (NeurIPS 2023) and PolyDiffuse (NeurIPS 2023): refinement/diffusion variants over the same regime — cite; include if code trivially runnable. CAGE (2025): edge-centric directed wall segments, 99.1% Room F1 on Structured3D; "directed" = geometric orientation, not access semantics; code pending. Raster2Seq (2026): see Lane 1 — nearest reconstruction competitor, mandatory baseline. PolyGraph (TVCG 2025): graph-based reconstruction from 3D scans — different input modality; cite. WAFFLE (WACV 2025): in-the-wild multimodal floorplan understanding; robustness evaluation source.

## 3.2 Floorplan→graph extraction
Tesseract (SIGSPATIAL 2025): see Lane 4 — Phase Zero backbone + heuristic-graph baseline. Raster-to-Graph (EG 2024): autoregressive structural-graph prediction + 10K dataset. Kim-Kim-Yu (ISPRS 2021): patch-tiling for large complex plans. Chen & Stouffs (2022): typed adjacency classification. Raster-to-Vector (ICCV 2017) + LIFULL: historical foundation; ResPlan (2025) documents the data-engineering overhead of large raw floorplan corpora — supports budgeting Phase Zero honestly.

## 3.3 Hierarchical 3D scene graphs (robotics)
3DSG (ICCV 2019); Hydra (RSS 2022); S-Graphs+; HOV-SG (RSS 2024: 100% floor-count retrieval, ~84% region recall on HM3DSem); HERO (2025: traversability under movable obstacles; watershed room partitioning from BEV occupancy); LLM-assisted 3DSG (2025); Catalano et al. (2025: flow/occupancy attributes from agent observation histories). Differentiation per Lane 3. Cited also as convergent validation of containment+peer edge design.

## 3.4 Floorplan graphs in generation and analysis
Graph2Plan (SIGGRAPH 2020), HouseGAN/++ (2020/21), HouseDiffusion (CVPR 2023): flat bubble-diagram conditioning at ~5-room scale. MSD (ECCV 2024): multi-unit residential; shows existing generators fail even at that step-up. Room-classification GNNs (2021): flat adjacency + GNN → room types. Graph-based generative floorplan embeddings (2020). SSIG (2023): IoU+GED similarity metric — adopted, not competed with. SceneScript (ECCV 2024), The Scene Language (CVPR 2025), OpenFunGraph (CVPR 2025): scenes-as-structured-representations trend at A* venues — validates framing; none address drawings, institutional scale, or physics.

## 3.5 Building physics ML
PINN building thermal modeling (2025 review); GNN-MPC HVAC control (2023–24, PhyGICS); LSTM/RNN multi-zone temperature prediction (2021–25); ANN large-venue zone estimation (2018). All sensor-dependent at inference. EnergyPlus + bim2sim are our labeling infrastructure.

## 3.5b Floorplan localization (Task L field)
LaLaLoc (ICCV 2021): latent layout localization from panoramas. LaLaLoc++ (ECCV 2022): global floorplan embedding, drops known-height assumptions. LASER (CVPR 2022): floorplan as point set, PointNet pose features vs circular image features. PF-Net (CoRL 2018), MCL (1999): particle-filter lineage. **F3Loc (CVPR 2024)**: 1D floorplan-ray observation model, monocular+multi-view depth fusion, SE(2) histogram filter; evaluated on Gibson(f) and Structured3D; recall@{0.1, 0.5, 1}m and @1m-30° conventions; open implementation — our integration base. **Semantic Rays (2025)**: adds room-type semantic rays; more than doubles F3Loc recall on Structured3D and ZInD — the published proof that structure-beyond-geometry helps FLoc; our HDG priors are the hierarchical continuation of exactly this trend. SPVLoc (ECCV 2024): semantic panoramic viewport matching. UnLoc (2025): depth-uncertainty modeling, LaMAR evaluation. 3DP, RSK, DisCo-FLoc (2025–26): geometric-prior/room-style/contrastive follow-ups within the F3Loc framework — confirms active subfield and stable evaluation conventions we adopt wholesale.

## 3.5c Egress and pedestrian flow simulation (Task E labeling infrastructure)
Social-force models (Helbing–Molnár lineage) and egress engineering tools (Pathfinder-class agent-based evacuation simulators; open alternatives: JuPedSim, Vadere) provide per-scenario evacuation traces from which we derive corridor load ranks, bottleneck identities, and relative clearance-time labels. Used exactly as EnergyPlus is used for Task T: automated supervision machinery, not a competing method. Graph-theoretic egress analysis (network-flow evacuation models in fire-safety engineering) supplies the mechanistic grounding: evacuation load concentrates on high-betweenness, capacity-limited corridor nodes — quantities our representation exposes directly.

## 3.6 Graph learning theory and architectures
Oversquashing (Alon & Yahav 2021; Topping 2022; Di Giovanni 2023); oversmoothing (Li 2018; Oono & Suzuki 2020); HGNet (2021: O(log n) hierarchical message paths); HC-GNN (2022); hierarchical GNNs for particle tracking (2023: better convergence/stability than flat); GHR (2026: out-of-range generalization — directly relevant since our test buildings exceed pretraining scale). Directionality: Dir-GNN (2023: separate in/out aggregation); directed-graph survey (2024: direction preservation raises expressiveness upper bound); MagNet lineage. Architectures we benchmark against as encoders: GCN, GAT, GraphSAGE (homogeneous flats); RGCN, HGT (typed/heterogeneous flats — HGT's node- and edge-type-dependent attention is the strongest "typed but non-hierarchical" comparator, with documented 9–21% gains over untyped baselines on heterogeneous benchmarks); Graphormer / GraphGPS (flat graph transformers — the strongest "transformer but non-hierarchical" comparator).

---

# 4. THE HDG REPRESENTATION

## 4.1 Two edge families on one node set
A building has two simultaneous relational structures; each alone is insufficient:

**Family 1 — Containment (organizational).** "Is-part-of" tree: room ⊂ corridor-cluster ⊂ zone/department ⊂ wing ⊂ building. Strictly level-adjacent; inherently directed (contains / contained-in). Encodes how the building is designed and operated (wards, compartments, access regimes).

**Family 2 — Physical adjacency (geometric reality).** Room↔room and room↔corridor relations from shared geometry, typed as wall-adjacent / door-connected / corridor-link. These live at leaf/corridor levels and cut across the hierarchy freely. A minority carry an access-direction attribute (one-way/controlled); most are bidirectional.

A pure tree cannot represent a cross-department door; a flat graph cannot represent that eight ICU rooms form one controlled ward. Both are needed; the 3DSG field independently converged on the same pattern.

## 4.2 Canonical worked example (appears in the paper)
ICU Wing ⊃ Corridor A ⊃ {ICU-1, ICU-2, Nurse Station}; Admin Wing ⊃ Corridor B ⊃ {Office, Records}. Real-world twist: the Nurse Station has a direct interior door to the Records Room — across wings.
Family-1 edges (9): Hospital→{ICU Wing, Admin Wing}; ICU Wing→Corr A; Admin Wing→Corr B; Corr A→{ICU-1, ICU-2, Nurse}; Corr B→{Office, Records}.
Family-2 edges (7): ICU-1↔ICU-2 (wall); five door-connected room↔corridor edges; **Nurse↔Records (door, cross-hierarchy)** — the edge a tree cannot hold and heat/traffic will actually use. If badge-controlled: additionally directed Nurse→Records.

## 4.3 Formal definition
```
HDG = (V, E_c, E_a, L, tau, delta, X)
V        nodes, with level map L: V -> {0 building, 1 wing/zone, 2 corridor, 3 room}
E_c      containment edges; (u,v) in E_c implies L(u) = L(v) - 1; forms a forest
E_a      adjacency edges; endpoints at levels {2,3}; cross-hierarchy allowed
tau:  E_a -> {wall-adjacent, door-connected, corridor-link}
delta: E_a -> {bidirectional, u->v, v->u}          (access direction)
X: V -> R^d  attributes. Room: type, area, aspect ratio, perimeter, normalized
     centroid. Corridor: length, connected-room count. Zone: aggregate area,
     room count, function label.
```
The paper reports per-building |V|, |E_a|, hierarchy depth, diameter, and degree distributions, contrasted with Structured3D/MSD — replacing rhetorical "complexity" with measured statistics.

---

# 5. THEORETICAL GROUNDING

**Hierarchy.** Flat message-passing provably suffers oversquashing (receptive-field information compressed into fixed-width states) and oversmoothing (representations converge to local averages), both worsening with graph diameter; a 120-room plan has a diameter far exceeding a 5-room flat. Hierarchical message passing is the documented remedy: HGNet guarantees message paths of at most logarithmic length between any connected pair; hierarchical GNN studies report improved convergence/stability. Our Family-1 tree is such a shortcut structure — and, unlike learned pooling, semantically meaningful (wards, wings), yielding interpretability for free.

**Direction.** Preserving directionality provably raises the expressiveness upper bound versus symmetrized graphs; Dir-GNN shows separate in/out aggregation yields gains exactly when relations are functionally asymmetric. Access-controlled doors are functionally asymmetric; symmetrizing them destroys information.

**Physics hypothesis (C2).** Mechanistic, from building science: inter-room heat exchange is mediated by shared walls/doors (Family-2 edges and types); HVAC zoning practice groups rooms by proximity and function (approximately Family-1 membership); circulation load concentrates on high-betweenness corridors (pure graph theory). The open question is effect size, answered empirically.

**Honest scope.** Theory licenses the design direction; it does not predict effect sizes for floorplans or thermal inference. The ablation grid (§11.4) measures them. Label: theory-guided experimentation.

---

# 6. DATA STRATEGY AND ANNOTATION BUDGET

This section exists to prevent one specific failure mode: building heavy annotation tooling, labeling thousands of images, and still training an under-fed transformer. The design below makes the manual effort small, bounded, and gate-protected, and shows why the model is adequately fed anyway.

## 6.1 Why 30–50 buildings is enough: supervision is per-node, not per-graph
Our learning tasks are node-level (thermal zone ID, temperature rank, room type — one label per room), edge-level (edge type, zone-boundary, direction — one label per edge), and subtree-level (hierarchy recovery). Every room and edge is a supervised example. Graph-level classification (which genuinely needs thousands of graphs) is not among our tasks. Standard node-classification research operates successfully at the 3K-node scale (e.g., Cora, 2.7K nodes); our gold corpus alone exceeds that, and our silver corpus exceeds it by ~25×.

## 6.2 Corpus targets (gold = human-verified; silver = automatic/simulation)

| Quantity | Minimum viable | Target | Notes |
|---|---|---|---|
| Buildings (ours) | 30 | 40–50 | LOBO evaluation needs ≥30 folds for stable statistics |
| Floor-plan images (ours) | ~90 | ~120–150 | assuming ~3 floors/building; each floor = one graph instance |
| Gold room nodes | 3,500 | ~4,800–6,000 | 30–50 bldgs × ~120 rooms |
| Gold corridor/zone/wing nodes | ~700 | ~1,100–1,400 | ~20 corridors + ~8 zones + ~2 wings per building |
| Gold Family-2 typed edges | ~9,000 | ~12,000–15,000 | ≈2.5× room count |
| Gold Family-1 edges | ≈ node count | ≈ node count | tree property |
| Gold directed-access edges | ≥300 | 500–800 | the rare class; verify class balance during Phase Zero |
| Silver room nodes (public + simulation labels) | 60,000 | 120,000+ | Structured3D ~20K; CubiCasa ~25K; MSD ~80–100K areas; all EnergyPlus/RC-labeled by our pipeline |
| Symbol-pretraining chunks | — | 40K+ | ArchCAD-400K partial release; no annotation needed |

**Supervision adequacy check.** A 2–8M-parameter hierarchical graph transformer fine-tuned on ~5K gold nodes after pretraining on >100K silver nodes is a conservative regime by current graph-learning standards; the risk is distribution shift (residential silver → institutional gold), not raw volume — mitigated by ArchCAD/FloorPlanCAD institutional pretraining and measured explicitly by the LOBO protocol.

## 6.3 Annotation economics
Per building (post-automatic-extraction *review*, not from-scratch tracing): Step-1 correction 30–90 min; Step-2 edge-type review 15–30 min; Step-3 hierarchy + direction 60–120 min; total 2–4 h/building. Corpus total: 80–200 h; **budget cap 160 h** = 2 annotators × 4 weeks × 20 h/wk. Inter-annotator agreement (Cohen's κ) measured on a 5-building dual-annotated subset; reported in the paper. If Experiment 0 (§7, Phase 0 gate) shows >4 h/building, the corpus is cut to the best-format subset rather than the budget expanded — the gate protects the timeline, not the other way around.

## 6.4 Tooling scope (deliberately minimal)
One thin web review UI over the extraction pipeline's JSON graph output (overlay graph on plan raster; merge/split rooms; toggle edge type; lasso-group rooms into zones; flag direction). Build budget: **≤5 working days**, using existing libraries. Explicitly out of scope: generic annotation platforms, crowdsourcing infrastructure, active-learning loops. If the UI estimate is exceeded, fall back to editing GeoJSON in QGIS — clunky but free.

## 6.5 Data augmentation multipliers (no annotation cost)
Dihedral geometric augmentation (8× rotations/reflections); scale jitter; zone-subgraph sampling (each building yields 6–10 zone subgraphs → 240–500 additional graph instances corpus-wide); ego-network sampling per node for contrastive pretraining; floor-level decomposition (each floor a separate instance). Optional, flagged-risk: synthetic institutional composition by stitching MSD units into pseudo-complexes — used only for pretraining, never evaluation, and reported transparently if used.

---

# 7. PHASE-BY-PHASE METHODOLOGY

Each phase lists inputs → outputs, tools, effort, and its exit gate. No phase starts before the previous phase's gate passes.

## Phase 0 — Feasibility gates (Week 1–2)
**Experiment 0 (extraction gate).** One building end-to-end through the raster lane: preprocess → Tesseract (or Raster-to-Graph, whichever performs better on a 1-floor pilot; Kim-style patch tiling if resolution demands) → typed-adjacency pass (Chen & Stouffs logic) → manual hierarchy layer in the review UI mock (spreadsheet acceptable at this stage). Record: automatic room recall; connectivity completeness (Tesseract's own metric, computed against a hand-checked reference); wall-clock human time per step. **Gate: ≥80% automatic room recall AND ≤4 h total human time.**
**Experiment 1 (baseline-failure gate).** Pretrained RoomFormer + PolyRoom inference on the same building (converted to their density-map input). Record Room Recall, OOM events. Also run Raster2Seq if code is released; else queue its reimplementation. **Gate: informational (any outcome proceeds; result shapes H1/H1b framing).**
**Experiment 2 (physics-signal gate).** One-week EnergyPlus (IFC lane) or RC-network (raster lane; nodes = rooms, inter-node resistance ∝ shared-wall length modulated by edge type, capacitance ∝ room area, diurnal exterior forcing) simulation on the same building. Test: do simulated per-room temperature profiles cluster in agreement with graph communities / zone membership (ARI of temperature-profile clustering vs Family-1 zones)? **Gate: ARI > 0.25 → full C2 program; 0.10–0.25 → C2 as secondary contribution; <0.10 → C2 demoted to negative-result section, representation paper proceeds.**

## Phase 1 — Corpus construction (Weeks 3–8, overlapping Phase 2)
Format triage of all buildings (raster / DXF-DWG / IFC lanes). Raster lane: Tesseract-based extraction with patch tiling; vector lane: geometry parsing to polygons + adjacency; IFC lane: direct entity extraction (also feeds bim2sim). Typed-adjacency pass on all. Hierarchy + direction annotation in the review UI under the §6.3 budget, with the 5-building κ subset dual-annotated first (early agreement check catches ambiguous guideline definitions before they contaminate the corpus — annotation guideline document is a Phase-1 deliverable). Privacy pass: redact identifying text (building names, room occupant names) from released rasters; confirm release permissions per building — buildings without release permission stay in train-only holdout, disclosed in the paper. Output: InstBuild v0 (graphs + rasters + stats + guidelines), train/val/test splits by building (never by floor — floors of one building are correlated).

## Phase 2 — Simulation labeling (Weeks 5–10)
IFC lane: bim2sim → EnergyPlus, annual simulation, extract per-room zone assignment, temperature time-series → rank labels, HVAC cluster. Raster/vector lanes: RC-network surrogate (as in Experiment 2) with parameters fitted to match EnergyPlus outputs on the IFC-lane subset (report fit quality — this validates the surrogate). Apply the same pipeline to Structured3D (3.5K scenes), CubiCasa5K, and MSD to produce the silver corpus (§6.2). Deliverable: label-generation code released with the benchmark.

## Phase 3 — Model development (Weeks 8–14)
Curriculum: (a) symbol/structure pretraining on ArchCAD-400K + FloorPlanCAD (masked node/edge-attribute prediction, edge-type prediction); (b) silver-label pretraining on simulation-labeled public corpora (thermal heads + centrality head); (c) gold fine-tuning on InstBuild with LOBO-compatible checkpoints. Encoder per §8. All ablation variants (§11.4) trained under identical budgets.

**Phase 3-L — Localization arm (Weeks 9–15, parallel track).** Integration base: the open F3Loc implementation, unchanged in its ray/depth/filter machinery — we modify only the prior. Design: (i) auto-derive HDGs for Structured3D, ZInD, and Gibson(f) from their vector ground-truth annotations (zero manual annotation; the hierarchy for residential scenes is shallow — building→room — which is honest and disclosed: these benchmarks test the *typed-structure* prior more than the deep-hierarchy prior); (ii) a coarse-to-fine scheme: the HDG encoder scores zone/room-level compatibility between observation features and node embeddings, producing a structural prior over the SE(2) grid that multiplies into F3Loc's histogram filter; (iii) train the compatibility head on the same splits F3Loc uses. Deliberately minimal surface area: one new prior term, everything else frozen or reproduced — reviewers can attribute any gain to the representation. Two ablations ship with it: flat room-label prior (reproducing the Semantic-Rays signal within our pipeline) vs full HDG prior; and prior-only vs filter-only. Exit gate (Week 12): if HDG prior does not beat flat-semantic prior on Structured3D validation recall@1m, Task L is reported as a negative/neutral result in supplementary and the paper leads with T+E — the arm is scoped so even this outcome costs ≤3 weeks of one track.

**Phase 3-E — Egress arm (Weeks 10–14, shares Phase-2 machinery).** Label generation: agent-based evacuation simulation (JuPedSim or Vadere; Pathfinder if licensed) on InstBuild and on MSD/Structured3D silver corpora — occupant seeding proportional to room area/type, standard egress parameters; extract per-corridor peak load ranks, bottleneck identities (top-k congestion nodes), and relative zone clearance times. Heads: corridor load ranking (pairwise ranking loss; Spearman rho vs simulation), bottleneck top-k identification (precision@k), zone clearance-time ordering. The betweenness head from the core model is the zeroth-order baseline the learned head must beat — a built-in "is learning adding anything over graph theory" check.

## Phase 4 — Evaluation campaign (Weeks 13–17)
Full baseline × dataset matrix (§10 × §9); ablation grid; statistical protocol (§11.5); complexity-statistics table; qualitative figures (one full-building HDG visualization; thermal-prediction heatmaps vs simulation; failure cases).

## Phase 5 — Writing and submission (Weeks 16–20)
Paper, supplementary (annotation guidelines, simulation configs, κ, per-building results), benchmark release packaging, code cleanup. Internal red-team review against Appendix A (every row must have its differentiation sentence in Related Work).

---

# 8. MODEL ARCHITECTURE AND TRAINING RECIPE

**Encoder — Hierarchical Heterogeneous Graph Transformer.** Leaf/corridor message passing over E_a with edge-type embeddings (tau) and direction-aware separate in/out aggregation where delta ≠ bidirectional (Dir-GNN-style); bottom-up pooling along E_c with learned per-level aggregation; cross-level attention (rooms attend to zone context); top-down broadcast so leaf predictions condition on global context. Parameter budget 2–8M. Positional/structural encodings: Laplacian eigenvectors on E_a + level embedding from L.

**Heads (one shared encoder, task-specific heads — the backbone claim is literal).** Task T: (1) thermal-zone clustering — node embedding + graph-contrastive loss; ARI/NMI vs simulation zones; (2) thermal rank — pairwise ranking loss; Spearman rho. Task E: (3) corridor egress-load ranking — pairwise ranking loss; Spearman rho vs evacuation simulation; (4) bottleneck top-k identification — precision@k. Task L: (5) observation–node compatibility head producing a structural prior over the SE(2) pose grid, multiplied into F3Loc's histogram filter (trained on FLoc benchmark splits; frozen F3Loc machinery). Shared/diagnostic: (6) corridor betweenness regression (self-supervised sanity check and Task-E zeroth-order baseline; Pearson r); (7) room-type classification and hierarchy-recovery heads for representation-quality experiments. Multi-task training: T/E heads jointly with uncertainty-weighted losses; L head fine-tuned separately on FLoc data (different input pairing: observation features + graph).

**Training.** AdamW; cosine schedule; dropout + DropEdge on E_a; early stopping on val ARI; 3 seeds everywhere. Compute envelope: single 24–48GB GPU suffices at this graph scale (largest graph ~200 nodes/floor; whole-building graphs ~600 nodes) — no distributed training required; report total GPU-hours in the paper.

---

# 9. DATASET INVENTORY

| Dataset | Scale | Regime | Role | Access | Size |
|---|---|---|---|---|---|
| Structured3D | 3,500 scenes; avg 5.79, max 22 rooms | synthetic residential | baseline train/eval; silver thermal labels | form: structured3d-dataset.org; RoomFormer-preproc on HF (Gen3DF/Structured3D) | ~196 GB full; preproc subset ≪ |
| RPLAN | 80K plans, ~5 rooms | real residential | generation baselines | form via project page (rplanpy pointers) | ~3.5 GB |
| MSD | 5,372 plans / 18.9K units | multi-unit residential | closest-complexity contrast; silver labels | free: data.4tu.nl; github.com/caspervanengelenburg/msd | ~2–3 GB |
| CubiCasa5K | 5K plans | residential (FI) | symbol pretrain; Raster2Seq comparison; silver labels | free direct: github.com/CubiCasa/CubiCasa5k | ~2 GB |
| FloorPlanCAD | 15K+ plans | mixed incl. hospitals, malls | institutional symbol pretrain | form: floorplancad.github.io; HF mirror Voxel51/FloorPlanCAD | ~5–10 GB |
| ArchCAD-400K | 5,538 drawings / 413K chunks; avg 11,000 m²; 86% non-residential | institutional/commercial CAD | large-scale structure pretrain | HF: ArchiAI-LAB/ArchCAD (40K live) | ~5 GB partial |
| ZInD (Zillow Indoor) | 71.5K panos / 2.7K homes with floorplans | residential, real | **Task-L evaluation set** (Semantic Rays reports here); HDGs auto-derived from vector GT | request via Zillow GitHub | large (panos) |
| Gibson(f) | F3Loc's split of Gibson scenes with floorplans | residential/office scans | **Task-L evaluation set** (F3Loc's primary benchmark) | via F3Loc repo instructions | moderate |
| Raster-to-Graph dataset | ~10K plans | residential | extraction-tool evaluation; extra eval (Raster2Seq reports on it) | github.com/SizheHu/Raster-to-Graph | ~1–2 GB |
| SESYD | synthetic document floorplans | synthetic | Tesseract's public eval set — extraction-lane sanity checks | free (classic dataset) | small |
| ResPlan | 17K vector-graph plans | residential | additional graph-format pretrain source | per arXiv 2508.14006 release | TBD |
| WAFFLE | in-the-wild | diverse | robustness eval | per WACV 2025 page | TBD |
| **InstBuild (ours)** | 30–50 buildings; 100+ rooms each; ~120–150 floor images | **institutional** | **primary benchmark: HDG annotations + simulation labels** | release with paper (permission-gated subset) | TBD |

Simulation infrastructure: EnergyPlus (energyplus.net) + bim2sim (github.com/BIM2SIM/bim2sim) + our RC-network surrogate (released).

---

# 10. BASELINE SUITE

Three baseline classes, each answering a distinct question.

## 10.A Reconstruction baselines — "can existing methods even see our buildings?"
| Method | Venue | Code | What it tests |
|---|---|---|---|
| Raster2Seq ★ | 2026 | arxiv.org/abs/2602.09016 (monitor; reimplement decoder if unreleased) | newest ceiling-free architecture vs institutional complexity; geometry ≠ understanding |
| RoomFormer | CVPR 23 | github.com/ywyue/RoomFormer ✓pretrained | query-ceiling failure |
| PolyRoom | ECCV 24 | github.com/3dv-casia/PolyRoom ✓pretrained | ceiling + benchmark-overfit check |
| HEAT | CVPR 22 | github.com/woodfrog/heat ✓pretrained | corner-pipeline collapse on dense layouts |
| FRI-Net | ECCV 24 | check release | implicit-field variant (Raster2Seq benchmarks it) |
| Floor-SP | ICCV 19 | github.com/woodfrog/floor-sp | non-neural, no-ceiling reference |
| CAGE | 2025 | pending | include if released; else cite |
| HouseDiffusion | CVPR 23 | github.com/aminshabani/house_diffusion | flat-graph generation breaks at scale |

## 10.B Representation baselines — "given a graph, is OUR graph the right one?" (all trained by us, identical heads/budgets)
| Encoder/graph | What it isolates |
|---|---|
| Tesseract heuristic graph + best flat encoder | competent flat extraction vs HDG: value of functional hierarchy + typing + direction |
| GCN / GAT / GraphSAGE on flat E_a | homogeneous-flat floor |
| RGCN / HGT on typed flat E_a | typing without hierarchy (HGT = strongest such comparator) |
| Graphormer / GraphGPS on flat E_a | transformer without hierarchy |
| Hydra-style geometric hierarchy (floors/rooms only) | geometric vs functional hierarchy (H4b) |
| Full HDG + our encoder | the proposed system |

## 10.C Localization baselines (Task L) — "does structured prior beat geometry and flat semantics?"
| Method | Venue | Code | Role |
|---|---|---|---|
| F3Loc | CVPR 2024 | open implementation ✓ | integration base and primary comparison; reproduce reported numbers first |
| Semantic Rays | 2025 | check release; reproduce flat-label prior within our pipeline regardless | the flat-semantics comparator our HDG prior must beat — the paper's key Task-L contrast |
| LASER | CVPR 2022 | public implementation ✓ | point-set representation comparator |
| LaLaLoc++ | ECCV 2022 | check release; cite numbers minimum | global-embedding comparator |
| F3Loc + uniform prior (ablation) | — | ours | isolates prior contribution from filter |

## 10.D Physical/operational-inference baselines — "is the signal real and non-trivial?"
| Baseline | What it tests |
|---|---|
| Spatial k-NN / proximity clustering | is thermal zoning just distance? |
| Area/type heuristics (rooms grouped by function labels) | is it just room type? |
| Random / majority | floor |
| PINN-style thermal (reference, reimplemented minimal) | documents sensor-dependent methods cannot run zero-sensor (framing row) |

---

# 11. METRICS AND STATISTICAL PROTOCOL

## 11.1 Reconstruction (community-standard)
Room/Corner/Angle precision, recall, F1 (IoU ≥ 0.5 room match; 5 px corner; 5° angle). Room Recall reported **as a function of building size** (recall-vs-rooms curve = the scale exhibit). Semantic room-type macro-F1. Inference time and peak GPU memory vs room count.

## 11.2 Topology (ours; flat polygon outputs cannot score here)
Graph Edit Distance (predicted vs GT adjacency); SSIG; Edge-Type Accuracy (tau); direction accuracy (delta, reported on the access-controlled subset with class-imbalance-aware metrics — precision/recall of the rare directed class); Hierarchy Recovery F1 (Family-1 containment); topological diameter error; corridor betweenness Pearson r; navigational completeness (Tesseract's metric — pairwise room-connection coverage) for extraction-quality comparability.

## 11.3 Physical field (Task T)
Thermal Zone ARI **and NMI** vs simulation zones; per-room temperature Spearman rho; zone-boundary edge F1; thermal cluster purity vs HVAC labels; Leave-One-Building-Out ARI/NMI.

## 11.3b Localization (Task L — community conventions adopted unchanged)
Recall @ 0.1 m, 0.5 m, 1 m; recall @ 1 m + 30° orientation; median localization error; sequence-mode filtered recall (F3Loc protocol); reported per dataset (Structured3D, ZInD, Gibson-f) with the F3Loc/Semantic-Rays splits. Stratified analysis by scene ambiguity (number of geometrically near-duplicate rooms) — the stratum where structural priors should matter most, and the bridge argument to institutional buildings.

## 11.3c Egress (Task E)
Corridor load-rank Spearman rho vs evacuation simulation; bottleneck identification precision@k (k=5,10); zone clearance-time ordering accuracy; improvement over the raw betweenness baseline (the learned-vs-graph-theory delta is the headline number for this arm).

## 11.4 Ablation grid (every metric × every condition)
full HDG · no hierarchy (flat E_a) · no direction (delta symmetrized) · no edge types (tau collapsed) · no node attributes (pure topology) · geometry-only (attributes, no edges) · geometric-hierarchy-only (Hydra-style). Full-vs-flat and full-vs-geometric-hierarchy carry claims C1/C2.

## 11.5 Statistical protocol
3 random seeds × LOBO folds (≥30 buildings → ≥30 folds); report mean ± std; paired Wilcoxon signed-rank across folds for headline comparisons, significance at p<0.05 with Holm correction across the ablation family; annotation quality reported as Cohen's κ on the dual-annotated subset; dataset statistics table (per-building |V|, |E_a|, depth, diameter, degree distribution) contrasted with Structured3D/MSD.

---

# 12. HYPOTHESES

| # | Hypothesis | Test | Risk |
|---|---|---|---|
| H1 | Query-based reconstruction (RoomFormer/PolyRoom/HEAT) collapses on institutional plans (Room Recall < 30%) | pretrained inference on InstBuild | Low |
| H1b | Raster2Seq either degrades materially on institutional plans (Room F1 −20 pts vs its residential scores) or retains geometry while scoring ~0 on §11.2 topology metrics | run/reimplement on InstBuild | Medium — informative either way |
| H2 | HDG encoder maintains Room-node task performance at 100+ rooms (type macro-F1 within 10 pts of its ≤25-room performance) | ours, size-stratified | Medium |
| H3 | Topology alone predicts thermal zoning (ARI > 0.4; random ≈ 0.1) | Group-3 protocol | High — headline bet, gate-protected by Experiment 2 |
| H4 | Functional hierarchy beats flat graph by >10 ARI on thermal | ablation | Medium |
| H4b | Functional hierarchy beats geometric-only hierarchy on thermal ARI and hierarchy-recovery | ablation | Medium |
| H4c | Typed+directed edges beat untyped/undirected on edge-dependent tasks (zone-boundary F1, direction-sensitive centrality) | ablation | Medium |
| H5 | LOBO generalization: ARI drop < 0.1 vs in-distribution | LOBO | High |
| H6 | Silver→gold transfer: silver pretraining improves gold fine-tuned ARI by >5 pts vs from-scratch | training ablation | Low–Medium |
| H7 | HDG structural prior improves FLoc over F3Loc-uniform AND over flat room-label prior (recall@1m on Structured3D and ZInD), with the largest gains in the high-ambiguity stratum | Task-L protocol, external benchmarks, real pose GT | Medium — gate at Week 12 (Phase 3-L); negative outcome is publishable-in-supplementary, not fatal |
| H8 | Topology predicts egress structure: learned load ranking beats raw betweenness by >0.1 Spearman; bottleneck precision@5 > 0.6 | Task-E protocol vs evacuation simulation | Medium |

Scope note: H1 is executed as a compact motivating experiment (one table, pretrained checkpoints only) rather than a full campaign — Raster2Seq has already published the residential-scale degradation curve, and the freed weeks fund the Task-L arm.

---

# 13. VENUE FIT ANALYSIS

**Why CVPR is a defensible primary target.** Precedent classes all present at recent CVPRs: floorplan structured prediction (RoomFormer CVPR 23; HouseDiffusion CVPR 23; ZInD dataset paper CVPR 21); scenes-as-structured-representations (The Scene Language CVPR 25; OpenFunGraph CVPR 25 Highlight); benchmark+task contributions with vision front-ends. Our vision component is genuine (extraction from raster drawings; structured prediction from images to graphs), and C2 is positioned as scene understanding beyond geometry — squarely in the functional-scene-graph trend line. The CV4AEC workshop (CVPR-co-located, floorplan reconstruction in scope, NSS 2026 challenge) confirms an active CVPR-adjacent community and provides a soft-landing venue for early results — but the main-conference target stands on the precedents above.

**Reviewer-risk at CVPR and its mitigation.** Risk: "this is building science / GIS, not vision." Mitigation baked into the paper structure: the input is images/drawings (vision), the core contribution is a representation + structured prediction problem (vision), the evaluation includes standard reconstruction metrics against CVPR-lineage baselines (vision), and physics labels come from an automated pipeline presented as supervision machinery, not as the paper's field. Tesseract's SIGSPATIAL provenance is cited as infrastructure, keeping our contribution clearly in the learning/representation layer.

**The Task-L arm as venue-fit repair.** Three chronic objections are answered by a single localization result on public benchmarks: (1) *"everything is evaluated on your own private benchmark"* — Task L runs on Structured3D/ZInD/Gibson-f against F3Loc's published numbers; (2) *"where is the vision?"* — Task L consumes camera observations and improves a CVPR 2024 vision system; (3) *"your physics labels are circular"* — Task-L ground truth is real camera poses with no simulation anywhere in the loop. The narrative also inherits a published trend (flat semantics already double F3Loc recall) and presents the HDG as its structured continuation — a framing reviewers can verify rather than take on faith.

**Why ICLR is the right alternate.** If Experiment 2 lands strongly, the ICLR framing writes itself: theory-guided hierarchical/directional representation learning with a new domain and a falsifiable structure-encodes-physics hypothesis, ablated against HGT/GraphGPS — a representation-learning story with unusual real-world grounding. Decision point: end of Phase 0 (gates determine which story is strongest); CVPR 2026 deadline (~mid-Nov 2025) precedes ICLR 2026 (~late Sept 2026 for the following cycle), so CVPR is attempted first and ICLR is the strengthened-resubmission path, not a simultaneous target.

---

# 14. RISK REGISTER

| Risk | P | Impact | Mitigation |
|---|---|---|---|
| Raster2Seq geometry survives our buildings | M | pure-scale story weakens | already repositioned; H1b informative both ways; topology metrics are representation-dependent |
| Another complexity paper lands pre-deadline | M | reconstruction novelty erodes further | field trajectory (MSD→WAFFLE→Raster2Seq) makes this real; C2+C1 functional-hierarchy moat unaffected; lock Experiments 0–2 evidence early |
| H3 fails (Experiment-2 gate < 0.10) | M | headline loss | scenario ladder: representation+benchmark paper with honest negative-result section remains viable |
| Phase-Zero cost blows the gate | M | timeline | corpus cut to best-format lanes; hierarchy annotation parallelizable; tooling capped at 5 days |
| Reviewers cite Hydra/3DSG | H | framing challenge | §2 Lane-3 scoping + H4b experiment answers with data |
| Reviewers cite Tesseract as "graph extraction exists" | M | framing challenge | Tesseract is our infrastructure AND a baseline row — the comparison quantifies exactly what it lacks |
| EnergyPlus one-zone-per-room too coarse | M | Group-3 validity | multi-zone models on IFC subset; RC-surrogate validated against E+; label-sensitivity analysis reported |
| Simulation-only supervision questioned | H | Group-3 credibility | pursue any real data (bills, HVAC maps) for 1–2 buildings as anchor (§16 Q4) |
| Class imbalance in directed edges | M | H4c power | verified during Phase 1 (≥300 directed edges target); imbalance-aware metrics |
| Release-permission gaps on buildings | M | benchmark scope | permission-gated release tiering, disclosed |
| Task-L integration overruns (F3Loc codebase, dataset prep) | M | timeline | deliberately minimal surface (one prior term, frozen filter); Week-12 gate; arm capped at one parallel track |
| HDG prior ≤ flat-label prior on FLoc (H7 fails) | M | Task-L headline | disclosed-in-supplementary outcome; paper leads T+E; residential FLoc benchmarks have shallow hierarchy — stated a priori as the hard setting for our prior |
| Three-task scope dilutes depth | M | review quality | hard cap at three arms; H1 reduced to compact table; rescue/crowd-ops confined to discussion |
| Egress simulator licensing (Pathfinder) | L | Task-E labels | open alternatives (JuPedSim, Vadere) are the default plan |

---

# 15. TIMELINE (20 working weeks to CVPR deadline)

Weeks 1–2: Phase 0 (Experiments 0/1/2; gates). Parallel: dataset downloads, Raster2Seq code watch + reimplementation start, format triage.
Weeks 3–8: Phase 1 corpus construction (κ subset first).
Weeks 5–10: Phase 2 simulation labeling (silver corpus).
Weeks 8–14: Phase 3 model development (pretrain → silver → gold curriculum; ablation variants).
Weeks 9–15: Phase 3-L localization arm (parallel track; F3Loc reproduction by Week 10; HDG-prior gate at Week 12).
Weeks 10–14: Phase 3-E egress arm (evacuation-simulation labeling shares Phase-2 infrastructure; heads join multi-task training).
Weeks 13–17: Phase 4 evaluation campaign.
Weeks 16–20: Phase 5 writing, packaging, red-team, submission.

---

# 16. OPEN QUESTIONS (BLOCKING — ANSWERS SHAPE PHASE 0)

1. Building typology (hospital/campus/office/mixed)? — selects the most credible physics task and expected baselines.
2. Floorplan formats per building (raster/DXF/IFC)? — determines lane assignment and Phase-Zero cost.
3. Existing annotations on drawings (room labels, legends)? — bootstraps hierarchy annotation.
4. Any real physical data (energy bills, HVAC zone maps, sensor logs) for even one building? — single strongest Group-3 upgrade.
5. Release permissions per building? — benchmark tiering.
6. Team capacity (annotator-hours/week; GPU access)? — validates §6.3 budget and §15 schedule.

---

# 17. APPENDIX A — CITATION-SAFETY TABLE

| Work | Cite because | Differentiation sentence |
|---|---|---|
| Raster2Seq (2026) | nearest reconstruction competitor; published complexity-degradation finding | flat polygon sequences at residential complexity, reconstruction-only; we contribute functional structured representation, institutional scale, physical inference |
| Tesseract (SIGSPATIAL 2025) | flat navigable-graph extraction from low-semantic plans; our Phase-Zero backbone | heuristic connectivity for navigation; no hierarchy, typing-for-learning, direction semantics, or inference — quantified as a baseline row |
| Hydra / 3DSG / HOV-SG / HERO | containment+peer hierarchical graphs exist | sensor-stream input, geometric hierarchy, navigation purpose; ours: drawings, functional hierarchy, directed access, physics |
| RoomFormer / PolyRoom / HEAT / FRI-Net / CAGE / Floor-SP / MonteFloor / SLIBO-Net / PolyDiffuse | reconstruction lineage | ceilings or flat outputs; no relations, hierarchy, or physics |
| Raster-to-Graph / Kim 2021 / Chen & Stouffs | extraction infrastructure | we extend with functional hierarchy + direction they do not attempt |
| MSD / WAFFLE / ArchCAD / FloorPlanCAD / ZInD / ResPlan / SESYD | dataset landscape | none institutional-graph + physics-labeled; InstBuild fills this |
| Graph2Plan / HouseGAN++ / HouseDiffusion | flat-graph conditioning precedent | ~5-room bubbles; breaks at scale |
| PINN / GNN-HVAC / LSTM thermal literature | adjacent physics ML | sensor-dependent at inference; we are zero-sensor |
| Oversquashing–oversmoothing + HGNet/HC-GNN; Dir-GNN + directed survey; HGT; GraphGPS/Graphormer | theory + architecture grounding | we apply, and benchmark against, established components; novelty is domain, representation semantics, and task |
| SSIG / GED | evaluation | adopted |
| SceneScript / Scene Language / OpenFunGraph | A*-venue structured-scene trend | validates framing; none address drawings, institutional scale, physics |
| F3Loc / LASER / LaLaLoc(++) / SPVLoc / UnLoc / 3DP / RSK / DisCo-FLoc | FLoc field and evaluation conventions | geometry-only or flat-semantic priors; we contribute structured functional priors within their own protocol |
| Semantic Rays (2025) | published proof that semantics improve FLoc | flat room labels; our HDG is the hierarchical/typed continuation — and their prior is reproduced as our key comparator |
| Social-force / JuPedSim / Vadere / Pathfinder; network-flow egress models | Task-E labeling infrastructure and mechanistic grounding | simulation machinery, not competing methods; learned head must beat raw betweenness |

# 18. APPENDIX B — DATA BUDGET WORKSHEET (assumptions explicit, update after Experiment 0)

Assumptions: 40 buildings; 3 floors/building avg; 120 rooms/building avg; 20 corridors, 8 zones, 2 wings/building; Family-2 ≈ 2.5× rooms; review times per §6.3 mid-range (3 h/building).
Derived: 120 floor images; 4,800 gold rooms; 1,200 aux nodes; 12,000 typed edges; 120 annotator-days? No: 40 × 3 h = 120 h ≈ 15 annotator-days ≈ 3 weeks for one annotator or 1.5 for two.
Silver: Structured3D 3,500 × 5.79 ≈ 20K rooms; CubiCasa 6,281 × ~4 ≈ 25K; MSD 18.9K units × ~4.5 areas ≈ 85K → ~130K silver room nodes.
Sanity: gold-to-parameter ratio for a 4M-param model is poor in isolation (as for all fine-tuning regimes) but standard under pretraining; the operative ratios are silver:parameters (~1:30 tokens-equivalent, comfortable) and gold nodes per class per task (thermal zones ~8/building × 40 = 320 zone instances; room types ~15 classes × ~300 instances/class), both adequate for the reported statistical protocol.
Kill-criteria restated: <80% extraction recall or >4 h/building at Experiment 0 → corpus reduction, not budget expansion; Experiment-2 ARI <0.10 → C2 demotion, not project abandonment.

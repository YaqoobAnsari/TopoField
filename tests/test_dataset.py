"""HDG ingestion: load a corpus, LOBO splits (by building), batch adapter."""

import json
from pathlib import Path

import pytest

from topofield.data import HDGDataset, generate_corpus, group_by_building, load_hdg_dir
from topofield.data.dataset import building_id_of
from topofield.graph import validate


def test_dataset_load_and_lobo(tmp_path):
    generate_corpus(tmp_path, n_buildings=5, seed0=0, n_wings=3)
    ds = HDGDataset(tmp_path)
    assert len(ds) == 5
    assert ds.num_buildings() == 5  # synthetic building_ids are unique
    folds = list(ds.lobo_splits())
    assert len(folds) == 5
    for _building, train, test in folds:
        assert len(test) == 1 and len(train) == 4
        assert set(train) | set(test) == set(range(5))  # a partition
        assert not (set(train) & set(test))
    t = ds.to_tensors(0)
    assert "x" in t and "room_mask" in t


def test_group_by_building_partitions(tmp_path):
    generate_corpus(tmp_path, n_buildings=3)
    graphs = load_hdg_dir(tmp_path)
    groups = group_by_building(graphs)
    assert sum(len(v) for v in groups.values()) == 3


def test_building_id_precedence():
    g = {
        "metadata": {"building_id": "bldg_X"},
        "nodes": [],
        "containment_edges": [],
        "adjacency_edges": [],
    }
    assert building_id_of(g) == "bldg_X"
    g2 = {"metadata": {}, "nodes": [{"id": "b", "level": 0, "attrs": {"name": "named"}}]}
    assert building_id_of(g2) == "named"


def test_invalid_graph_in_dir_raises(tmp_path):
    (tmp_path / "bad.hdg.json").write_text(
        json.dumps({"version": "0.1", "nodes": [], "containment_edges": [], "adjacency_edges": []})
    )
    with pytest.raises(ValueError):
        load_hdg_dir(tmp_path)  # empty nodes -> schema invalid


_REAL_RESULTS = Path(__file__).parents[1] / "third_party/tesseract/Results/Json"


@pytest.mark.skipif(not _REAL_RESULTS.exists(), reason="Tesseract results not present")
def test_batch_convert_real_results(tmp_path):
    from topofield.extraction.batch import convert_tesseract_results

    written = convert_tesseract_results(_REAL_RESULTS, tmp_path)
    assert written, "expected at least one converted HDG"
    for p in written:
        assert validate(json.loads(p.read_text())).ok

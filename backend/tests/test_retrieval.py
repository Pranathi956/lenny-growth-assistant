from app.agent.rag import TranscriptIndex


def test_index_finds_relevant_chunk(tmp_path):
    d = tmp_path / "transcripts"
    d.mkdir()
    (d / "ep1.txt").write_text("Activation metrics should correlate with week four retention.")
    (d / "ep2.txt").write_text("Pricing experiments should be evaluated on cohort level LTV.")

    index = TranscriptIndex(str(d))
    results = index.search("how should I choose an activation metric", top_k=2)

    assert len(results) > 0
    assert results[0][0].title == "ep1"


def test_empty_index_returns_no_results(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    index = TranscriptIndex(str(d))
    assert index.search("anything") == []

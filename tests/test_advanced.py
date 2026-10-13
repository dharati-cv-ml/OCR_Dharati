from app.advanced import summarize

def test_empty_summary():
    assert summarize([])['pass_rate'] == 0

def test_summary_counts():
    result = summarize([{'passed':True,'processing_ms':20,'barcodes':[{'text':'x'}]}, {'passed':False,'processing_ms':40,'barcodes':[]}])
    assert result['passed'] == 1
    assert result['needs_review'] == 1
    assert result['pass_rate'] == 50
    assert result['mean_processing_ms'] == 30
    assert result['codes_found'] == 1

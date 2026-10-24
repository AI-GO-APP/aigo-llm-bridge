from tools.tests.run_native_update import safe_probe


def test_native_failure_diagnostics_never_echo_payloads_or_credentials():
    value={'success':False,'stage':'native_csv_export','failure_type':'private-secret',
        'token':'private-secret','checks':{'native_csv_exact_metadata_columns':False,
            'private-secret':True,'key_not_stored_plaintext':'private-secret'}}
    assert safe_probe(value)=={'success':False,'stage':'native_csv_export',
        'checks':{'native_csv_exact_metadata_columns':False}}
    assert safe_probe({'stage':'private-secret'})['stage']=='unknown'

from desktop_bridge.byo import main
if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--schema-validate']:
        from desktop_bridge.schema_guard import main as validate
        validate()
    else:raise SystemExit(main())

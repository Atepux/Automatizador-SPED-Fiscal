"""Abrir a interface nao acessa o PVA; acoes dependem dos botoes do usuario."""
import sys
from app.runtime import setup_streams,prepare_bridge

if __name__=='__main__':
    setup_streams()
    if len(sys.argv)>1 and sys.argv[1]=='--sped-worker':
        from worker_entry import dispatch
        dispatch()
    elif len(sys.argv)>1 and sys.argv[1]=='--autoteste':
        from app.selftest import main
        sys.exit(main())
    else:
        prepare_bridge()
        from app.gui import main
        main()

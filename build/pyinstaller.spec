# -*- mode: python ; coding: utf-8 -*-

a = Analysis(  # noqa: F821  # type: ignore[name-defined]
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons'), ('version.json', '.')],
    hiddenimports=[
        'app.frontend.modules.barcode_pdf.view',
        'app.frontend.modules.cofanet.view',
        'app.frontend.modules.ksh.view',
        'app.frontend.modules.merkantil.view',
        'app.frontend.modules.mouse_mover.view',
    ],
    hookspath=['build/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821  # type: ignore[name-defined]
exe = EXE(  # noqa: F821  # type: ignore[name-defined]
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DataProcessingTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,
)

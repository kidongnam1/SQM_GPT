# -*- coding: utf-8 -*-
"""patch_revert_backend.py — AVAILABLE → PENDING revert endpoint를 inbound.py 끝에 추가"""
from pathlib import Path

f = Path('backend/api/inbound.py')
src = f.read_text(encoding='utf-8')

MARKER = '@router.post("/confirm/{lot_no}", summary="\u2705 \uc785\uace0 \ud655\uc815 (PENDING \u2192 AVAILABLE)")'

if '/revert/{lot_no}' in src:
    print("\uc774\ubbf8 \ucd94\uac00\ub428 \u2014 \uc2a4\ud0b5")
else:
    NEW_ENDPOINT = '''

# \u2500\u2500 AVAILABLE \u2192 PENDING \uc785\uace0 \ucde8\uc18c \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@router.post("/revert/{lot_no}", summary="\u21a9\ufe0f \uc785\uace0 \ucde8\uc18c (AVAILABLE \u2192 PENDING)")
def revert_to_pending(lot_no: str):
    """
    AVAILABLE \u2192 PENDING \uc804\ud658. \uc2e4\uc218\ub85c \uc785\uace0 \ud655\uc815\ud55c \uacbd\uc6b0 \ucde8\uc18c \uc2dc \ud638\ucd9c.
    \uc548\uc804\uccb4\ud06c: RESERVED/PICKED/SOLD \ud1a4\ubc31\uc774 \uc5c6\uc5b4\uc57c \ucde8\uc18c \uac00\ub2a5.
    """
    try:
        db = _open_db()
        row = db.execute(
            "SELECT id, status FROM inventory WHERE lot_no=?", (lot_no,)
        ).fetchone()
        if not row:
            db.close()
            raise HTTPException(404, f"{lot_no} \uc5c6\uc74c")
        if dict(row)["status"] != "AVAILABLE":
            db.close()
            raise HTTPException(
                400, f"{lot_no}: AVAILABLE \uc0c1\ud0dc\uac00 \uc544\ub2d8 (\ud604\uc7ac: {dict(row)[\'status\']})"
            )
        blocked = db.execute(
            "SELECT COUNT(*) FROM inventory_tonbag WHERE lot_no=? AND status IN (\'RESERVED\',\'PICKED\',\'SOLD\')",
            (lot_no,)
        ).fetchone()[0]
        if blocked:
            db.close()
            raise HTTPException(
                400, f"{lot_no}: RESERVED/PICKED/SOLD \ud1a4\ubc31 {blocked}\uac1c \uc874\uc7ac \u2014 \ucde8\uc18c \ubd88\uac00"
            )
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "UPDATE inventory SET status=\'PENDING\', inbound_date=NULL, updated_at=? WHERE lot_no=? AND status=\'AVAILABLE\'",
            (ts, lot_no)
        )
        db.execute(
            "UPDATE inventory_tonbag SET status=\'PENDING\', updated_at=? WHERE lot_no=? AND status=\'AVAILABLE\'",
            (ts, lot_no)
        )
        db.commit()
        db.close()
        logger.info(f"[revert-pending] {lot_no} AVAILABLE \u2192 PENDING")
        return {
            "success": True,
            "lot_no": lot_no,
            "message": f"{lot_no} \u2192 PENDING \ub418\ub3cc\ub9ac\uae30 \uc644\ub8cc",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /revert/{lot_no} error: {e}")
        raise HTTPException(500, str(e))
'''
    src = src + NEW_ENDPOINT
    f.write_text(src, encoding='utf-8')
    print("revert endpoint \ucd94\uac00 \uc644\ub8cc")

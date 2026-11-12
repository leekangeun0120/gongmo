"""공모주 달력 자동 갱신 스크립트.

금융감독원 DART 오픈API로 최근 '증권신고서(지분증권)'와 정정 공시를 확인해서
data.json 에 새 종목을 추가하고, 일정이 바뀐 종목에 표시를 남긴다.

환경변수 DART_API_KEY 가 필요하다 (opendart.fss.or.kr 에서 무료 발급).
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
API = "https://opendart.fss.or.kr/api"


def get(path, **params):
    params["crtfc_key"] = os.environ["DART_API_KEY"]
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def norm(name):
    name = re.sub(r"\(주\)|㈜|주식회사|\s", "", name or "")
    # 스팩은 이름이 제각각이라 '증권사 앞 두 글자 + 스팩 + 번호'로 맞춘다
    # 예) 신영해피투모로우제12호기업인수목적 / 신영스팩12호 → 신영스팩12
    if "기업인수목적" in name or "스팩" in name:
        num = re.findall(r"(\d+)", name)
        if num:
            return f"{name[:2]}스팩{num[0]}".lower()
    return name.lower()


def recent_filings(days=45):
    """최근 발행공시(C) 중 지분증권 증권신고서와 정정본만 모은다."""
    today = datetime.now(KST)
    bgn = (today - timedelta(days=days)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    out, page = [], 1
    while True:
        res = get("list.json", bgn_de=bgn, end_de=end, pblntf_ty="C",
                  page_no=page, page_count=100)
        if res.get("status") == "013":  # 조회된 데이터 없음
            break
        if res.get("status") != "000":
            raise RuntimeError(f"DART 오류 {res.get('status')}: {res.get('message')}")
        for f in res.get("list", []):
            # 아직 상장 안 된 회사(E=기타, N=코넥스)만. 상장사의 유상증자는 제외
            nm = f.get("report_nm", "")
            # 철회신고서도 함께 본다 (공모를 접으면 이 서류가 올라옴)
            if ("증권신고서(지분증권)" in nm or "철회신고서" in nm) and f.get("corp_cls") in ("E", "N"):
                out.append(f)
        if page >= int(res.get("total_page", 1)):
            break
        page += 1
    out.sort(key=lambda f: f["rcept_no"])
    return out


def find_values(obj, key):
    """JSON 안 어디에 있든 key 값을 모두 찾는다 (DART 응답 구조가 바뀌어도 견디도록)."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and isinstance(v, str) and v.strip():
                found.append(v.strip())
            else:
                found += find_values(v, key)
    elif isinstance(obj, list):
        for v in obj:
            found += find_values(v, key)
    return found


def parse_period(text):
    """'2026년 11월 12일 ~ 2026년 11월 13일', '2026.11.12 ~ 11.13' 같은 글에서 날짜 두 개를 뽑는다."""
    nums = re.findall(r"(\d{4})?\D{0,3}?(\d{1,2})\D{1,3}(\d{1,2})", text)
    dates, year = [], None
    for y, m, d in nums:
        year = int(y) if y else year
        if year and 1 <= int(m) <= 12 and 1 <= int(d) <= 31:
            dates.append(f"{year:04d}-{int(m):02d}-{int(d):02d}")
    return (dates[0], dates[-1]) if dates else (None, None)


def detail(corp_code, rcept_dt):
    """증권신고서 주요정보에서 청약기일·주관사를 꺼낸다. 실패하면 빈 값."""
    try:
        res = get("estkRs.json", corp_code=corp_code, bgn_de=rcept_dt, end_de=rcept_dt)
    except Exception as e:  # noqa: BLE001
        print("  상세 조회 실패:", e)
        return {}
    if res.get("status") != "000":
        return {}
    info = {}
    sbd = find_values(res, "sbd")
    if sbd:
        info["s"], info["e"] = parse_period(sbd[-1])
    brokers = []
    for b in find_values(res, "actnmn"):
        b = re.sub(r"\(주\)|㈜|주식회사|\s", "", b)
        if b and re.search(r"[가-힣A-Za-z]", b) and b not in brokers:
            brokers.append(b)
    if brokers:
        info["b"] = brokers
    return info


def main():
    if not os.environ.get("DART_API_KEY"):
        print("DART_API_KEY 가 없어 건너뜀")
        return 0
    data = json.load(open(DATA, encoding="utf-8"))
    ipos = data["ipos"]
    by_name = {norm(x["n"]): x for x in ipos}
    # 화면 이름을 바꿔도 DART 이름으로 계속 찾도록
    by_name.update({norm(x["dart_name"]): x for x in ipos if x.get("dart_name")})
    notices = data.get("notices", [])
    seen_notice = {n["rcept_no"] for n in notices}
    changed = False
    quiet = set()

    for f in recent_filings():
        key = norm(f["corp_name"])
        rno, rdt = f["rcept_no"], f["rcept_dt"]
        is_fix = "정정" in f["report_nm"]
        x = by_name.get(key)
        if x and x.get("dart_seen", "") >= rno:
            continue
        if x and (not x.get("dart_seen") or key in quiet):
            quiet.add(key)
            # 처음 연결할 때는 조용히 공시 번호만 기억 (이미 정리된 종목)
            x["dart"] = x["dart_seen"] = rno
            changed = True
            continue
        print(f"{f['corp_name']} · {f['report_nm']} · {rno}")
        if "철회" in f["report_nm"]:
            if x is not None and not x.get("cancel"):
                x["cancel"] = f"{rdt[:4]}-{rdt[4:6]}-{rdt[6:]}"
                x["dart_seen"] = rno
                if rno not in seen_notice:
                    notices.insert(0, {"date": f"{rdt[4:6]}/{rdt[6:]}", "rcept_no": rno,
                                       "text": f"{x['n']} 상장 철회 (일반 청약 취소)"})
                    seen_notice.add(rno)
                changed = True
            continue
        info = detail(f["corp_code"], rdt)
        date_txt = f"{rdt[4:6]}/{rdt[6:]}"
        if x is None:
            today = datetime.now(KST).strftime("%Y-%m-%d")
            if not info.get("e") or info["e"] < today:
                print("  청약일이 없거나 이미 지난 종목이라 건너뜀")
                continue
            x = {"n": re.sub(r"\(주\)|㈜|주식회사", "", f["corp_name"]).strip(), "mk": "확인 중",
                 "d": "새로 신고된 종목이에요. 기업 설명은 곧 채워질 예정이에요.",
                 "s": None, "e": None, "b": [], "band": [0, 0], "new": True,
                 "dart_name": f["corp_name"]}
            if "스팩" in f["corp_name"]:
                x["spac"] = True
            ipos.append(x)
            by_name[key] = x
            text = f"{f['corp_name']} 증권신고서 제출 (새 공모주)"
        else:
            text = f"{f['corp_name']} 증권신고서 {'정정' if is_fix else '제출'} · 일정·가격 다시 확인"
            if is_fix:
                x["alert"] = f"{date_txt} 증권신고서 정정. 일정이나 가격이 바뀌었을 수 있어요."
        if info.get("s") and info["s"] != x.get("s"):
            x["s"], x["e"] = info["s"], info["e"]
        if info.get("b") and not x.get("b"):
            x["b"] = info["b"]
        x["dart"] = rno
        x["dart_seen"] = rno
        if rno not in seen_notice:
            notices.insert(0, {"date": date_txt, "rcept_no": rno, "text": text})
            seen_notice.add(rno)
        changed = True

    # 청약이 끝난 지 40일 넘은 종목은 정리
    cutoff = (datetime.now(KST) - timedelta(days=40)).strftime("%Y-%m-%d")
    keep = [x for x in ipos if not x.get("e") or x["e"] >= cutoff]
    if len(keep) != len(ipos):
        changed = True
    data["ipos"] = sorted(keep, key=lambda x: (x.get("s") or "9999"))
    data["notices"] = notices[:20]

    if changed:
        data["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M+09:00")
        data["updated_by"] = "DART 자동 확인"
        with open(DATA, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=1)
        print("data.json 갱신")
    else:
        print("바뀐 내용 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())

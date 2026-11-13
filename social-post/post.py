#!/usr/bin/env python3
"""GE4u free auto-poster: publishes the day's plan directly through each platform's official API.

Runs every 20 minutes from GitHub Actions. For today's date (Asia/Ho_Chi_Minh) it reads plan.json from
release media-D, posts every item whose time has come and that is not in the posted log yet, and writes
the log back to the same release (posted.json) so nothing is ever posted twice.

Platforms and the secrets each needs (a platform without its secrets is skipped, never an error):
  Instagram Reels   META_PAGE_TOKEN, IG_USER_ID
  Facebook Reels    META_PAGE_TOKEN, FB_PAGE_ID         (Instagram items are cross-posted here)
  Facebook promo    META_PAGE_TOKEN, FB_PAGE_ID         (marketing/promo-posts.json, with picture)
  Threads           THREADS_TOKEN, THREADS_USER_ID      (plan "threads" + promo copy)
  YouTube Shorts    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
TikTok is not posted here: TikTok only allows public API posts after an app audit. tiktok_pack.py prepares
the day's TikTok videos for TikTok Studio scheduling instead.

Usage: post.py [--date YYYY-MM-DD] [--dry-run] [--only instagram,facebook,threads,youtube,promo]
"""
import argparse, datetime as dt, json, os, pathlib, re, subprocess, sys, tempfile, time, urllib.parse
import urllib.request

VN = dt.timezone(dt.timedelta(hours=7))
REPO = os.environ.get("GITHUB_REPOSITORY", "ge4uhealthsciences-creator/medvocab-lab")
ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPH = "https://graph.facebook.com/" + os.environ.get("META_GRAPH_VERSION", "v25.0")
THREADS = "https://graph.threads.net/v1.0"
YT_DAILY_MAX = int(os.environ.get("YT_DAILY_MAX", "6"))       # default API quota ≈ 6 uploads/day
# While the quota allows only 6 uploads, use YouTube's best hours (Metricool best-time data: 14–17h, then 10h, 12h).
YT_HOURS = {int(h) for h in os.environ.get("YT_HOURS", "10,12,14,15,16,17").split(",")}
# Owner-approved plan (5 Nov 2026): 3 Reels a day on Instagram/Facebook. Older 12-Reel plans are thinned to these hours.
META_HOURS = {int(h) for h in os.environ.get("META_HOURS", "11,17,19").split(",")}
FB_DAILY_MAX = 30                                             # Meta: 30 API reels per Page per 24 h
LATE_LIMIT_MIN = int(os.environ.get("LATE_LIMIT_MIN", "180"))  # skip items more than 3 h overdue
THREADS_LIMIT = 500


# ---------------------------------------------------------------- http helpers
class ApiError(Exception):
    pass


def http(method, url, data=None, headers=None, raw=None, timeout=120):
    body = raw
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode() or "{}"
            ctype = r.headers.get("Content-Type", "")
            return json.loads(txt) if txt.strip().startswith(("{", "[")) else {"_text": txt, "_type": ctype}
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:600]
        raise ApiError(f"{method} {url.split('?')[0]} -> {e.code}: {msg}") from None


def env(*names):
    vals = [os.environ.get(n, "").strip() for n in names]
    return vals if all(vals) else None


# ---------------------------------------------------------------- release I/O
def release_url(date, name):
    return f"https://github.com/{REPO}/releases/download/media-{date}/{name}"


def gh(*args, check=True):
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def _release(date):
    r = gh("api", f"repos/{REPO}/releases/tags/media-{date}", check=False)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def _download(rel, name, workdir):
    a = next((x for x in rel["assets"] if x["name"] == name), None)
    if not a:
        return None
    out = workdir / name
    with open(out, "wb") as fh:
        subprocess.run(["gh", "api", "-H", "Accept: application/octet-stream", f"repos/{REPO}/releases/assets/{a['id']}"],
                       check=True, stdout=fh)
    return out


def load_plan(date, workdir):
    rel = _release(date)
    if not rel or not _download(rel, "plan.json", workdir):
        raise SystemExit(f"No release media-{date} with plan.json yet")
    workdir.joinpath("_release.json").write_text(json.dumps(rel))
    return json.loads((workdir / "plan.json").read_text())


def load_log(date, workdir):
    rel = json.loads((workdir / "_release.json").read_text())
    p = _download(rel, "posted.json", workdir)
    return json.loads(p.read_text()) if p else {"date": date, "posts": {}}


def save_log(date, log, workdir):
    p = workdir / "posted.json"
    p.write_text(json.dumps(log, ensure_ascii=False, indent=1))
    rel = _release(date)
    for a in rel["assets"]:
        if a["name"] == "posted.json":
            gh("api", "-X", "DELETE", f"repos/{REPO}/releases/assets/{a['id']}", check=False)
    gh("api", "-X", "POST", "-H", "Content-Type: application/json",
       f"https://uploads.github.com/repos/{REPO}/releases/{rel['id']}/assets?name=posted.json", "--input", str(p))


def download_asset(date, name, workdir):
    rel = json.loads((workdir / "_release.json").read_text())
    if not _download(rel, name, workdir):
        raise ApiError(f"asset {name} not in media-{date}")


# ---------------------------------------------------------------- platforms
def post_instagram(item, date, tok, ig_id):
    url = release_url(date, item["file"])
    c = http("POST", f"{GRAPH}/{ig_id}/media", {"media_type": "REELS", "video_url": url, "caption": item["caption"],
                                                "share_to_feed": "true", "access_token": tok})
    cid = c["id"]
    for _ in range(40):  # up to ~6.5 min of processing
        time.sleep(10)
        st = http("GET", f"{GRAPH}/{cid}?fields=status_code,status&access_token={urllib.parse.quote(tok)}")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise ApiError(f"Instagram processing {st.get('status_code')}: {st.get('status')}")
    else:
        raise ApiError("Instagram processing timed out")
    pub = http("POST", f"{GRAPH}/{ig_id}/media_publish", {"creation_id": cid, "access_token": tok})
    return pub["id"]


def post_facebook_reel(item, date, tok, page_id):
    url = release_url(date, item["file"])
    st = http("POST", f"{GRAPH}/{page_id}/video_reels", {"upload_phase": "start", "access_token": tok})
    vid = st["video_id"]
    up = http("POST", f"https://rupload.facebook.com/video-upload/{GRAPH.rsplit('/', 1)[1]}/{vid}",
              headers={"Authorization": f"OAuth {tok}", "file_url": url}, raw=b"")
    if not up.get("success"):
        raise ApiError(f"Facebook upload failed: {up}")
    fin = http("POST", f"{GRAPH}/{page_id}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                                          "description": item["caption"], "access_token": tok})
    if not fin.get("success"):
        raise ApiError(f"Facebook finish failed: {fin}")
    return vid


def post_facebook_photo(text, image_url, tok, page_id):
    data = {"caption": text, "access_token": tok}
    if image_url:
        data["url"] = image_url
        return http("POST", f"{GRAPH}/{page_id}/photos", data)["id"]
    return http("POST", f"{GRAPH}/{page_id}/feed", {"message": text, "access_token": tok})["id"]


def post_threads(text, topic, tok, uid):
    if len(text) > THREADS_LIMIT:
        raise ApiError(f"Threads text too long ({len(text)} > {THREADS_LIMIT})")
    data = {"media_type": "TEXT", "text": text, "access_token": tok}
    if topic:
        data["topic_tag"] = topic
    c = http("POST", f"{THREADS}/{uid}/threads", data)
    time.sleep(30)  # Meta recommends ~30 s before publishing
    return http("POST", f"{THREADS}/{uid}/threads_publish", {"creation_id": c["id"], "access_token": tok})["id"]


def post_instagram_image(caption, image_url, tok, ig_id):
    c = http("POST", f"{GRAPH}/{ig_id}/media", {"image_url": image_url, "caption": caption, "access_token": tok})
    for _ in range(12):
        st = http("GET", f"{GRAPH}/{c['id']}?fields=status_code&access_token={urllib.parse.quote(tok)}")
        if st.get("status_code") in (None, "FINISHED"):
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise ApiError(f"Instagram image {st.get('status_code')}")
        time.sleep(5)
    return http("POST", f"{GRAPH}/{ig_id}/media_publish", {"creation_id": c["id"], "access_token": tok})["id"]


def post_threads_image(text, image_url, topic, tok, uid):
    if len(text) > THREADS_LIMIT:
        raise ApiError(f"Threads text too long ({len(text)} > {THREADS_LIMIT})")
    data = {"media_type": "IMAGE", "image_url": image_url, "text": text, "access_token": tok}
    if topic:
        data["topic_tag"] = topic
    c = http("POST", f"{THREADS}/{uid}/threads", data)
    time.sleep(30)
    return http("POST", f"{THREADS}/{uid}/threads_publish", {"creation_id": c["id"], "access_token": tok})["id"]


def one_off_posts(date):
    """Dated one-off posts (e.g. a product announcement) from marketing/scheduled-posts.json."""
    try:
        posts = json.loads((ROOT / "marketing" / "scheduled-posts.json").read_text())["posts"]
    except Exception:
        return []
    return [p for p in posts if p.get("date") == date.isoformat()]


def yt_access_token(cid, secret, refresh):
    r = http("POST", "https://oauth2.googleapis.com/token", {"client_id": cid, "client_secret": secret,
                                                            "refresh_token": refresh, "grant_type": "refresh_token"})
    return r["access_token"]


def post_youtube(item, date, access, workdir):
    f = workdir / item["file"]
    if not f.exists():
        download_asset(date, item["file"], workdir)
    title = item.get("title") or item["caption"].split("\n")[0]
    if "#shorts" not in title.lower():
        title = (title[:91] + " #Shorts")
    meta = {"snippet": {"title": title[:100], "description": item["caption"], "categoryId": "27",
                        "tags": ["GE4u", item.get("discipline_en", ""), "Medical English"], "defaultLanguage": "en"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}}
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(f.stat().st_size)})
    try:
        with urllib.request.urlopen(init, timeout=60) as r:
            loc = r.headers["Location"]
    except urllib.error.HTTPError as e:
        raise ApiError(f"YouTube init -> {e.code}: {e.read().decode(errors='replace')[:400]}") from None
    put = urllib.request.Request(loc, data=f.read_bytes(), method="PUT", headers={"Content-Type": "video/mp4"})
    try:
        with urllib.request.urlopen(put, timeout=600) as r:
            return json.loads(r.read().decode())["id"]
    except urllib.error.HTTPError as e:
        raise ApiError(f"YouTube upload -> {e.code}: {e.read().decode(errors='replace')[:400]}") from None


# ---------------------------------------------------------------- TikTok (Content Posting API, Direct Post)
TT = "https://open.tiktokapis.com/v2"
TIKTOK_PRIVACY = os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY")  # unaudited apps may only post SELF_ONLY


TT_REDIRECT = os.environ.get("TIKTOK_REDIRECT_URI", "https://ge4u.trungminhle.com/")
TT_TOKEN_FILE = "tiktok/refresh.enc"  # refresh token, AES-256 encrypted with TIKTOK_CLIENT_SECRET, on branch status


def _crypt(text, secret, decrypt=False):
    args = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-a", "-A", "-pass", "env:TT_KEY"] + (["-d"] if decrypt else [])
    r = subprocess.run(args, input=text, capture_output=True, text=True, env={**os.environ, "TT_KEY": secret})
    if r.returncode:
        raise ApiError("TikTok token (de)crypt failed: " + r.stderr[:200])
    return r.stdout.strip()


def tiktok_refresh_token(secret):
    if os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip():
        return os.environ["TIKTOK_REFRESH_TOKEN"].strip()
    r = gh("api", f"repos/{REPO}/contents/{TT_TOKEN_FILE}?ref={STATUS_BRANCH}", "--jq", ".content", check=False)
    if r.returncode or not r.stdout.strip():
        return ""
    import base64
    return _crypt(base64.b64decode(r.stdout).decode(), secret, decrypt=True)


def _save_tiktok_refresh(tok, secret):
    _put_file(TT_TOKEN_FILE, _crypt(tok, secret) + "\n", "TikTok: update encrypted refresh token")


def tiktok_exchange_code(key, secret, code):
    """One-time: turn the ?code= from the TikTok login redirect into a stored refresh token."""
    code = urllib.parse.unquote(code.strip())
    r = http("POST", f"{TT}/oauth/token/", {"client_key": key, "client_secret": secret, "code": code,
                                            "grant_type": "authorization_code", "redirect_uri": TT_REDIRECT},
             headers={"Content-Type": "application/x-www-form-urlencoded"})
    if "refresh_token" not in r:
        raise ApiError(f"TikTok code exchange failed: {str(r)[:300]}")
    _save_tiktok_refresh(r["refresh_token"], secret)
    print("TikTok authorised, scopes:", r.get("scope"), "| refresh token stored encrypted on branch status")


def tiktok_access_token(key, secret, refresh):
    r = http("POST", f"{TT}/oauth/token/", {"client_key": key, "client_secret": secret,
                                            "grant_type": "refresh_token", "refresh_token": refresh},
             headers={"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in r:
        raise ApiError(f"TikTok token refresh failed: {str(r)[:300]}")
    if r.get("refresh_token") and r["refresh_token"] != refresh and not os.environ.get("TIKTOK_REFRESH_TOKEN"):
        try:
            _save_tiktok_refresh(r["refresh_token"], secret)
        except Exception as e:
            print("WARN: new TikTok refresh token not saved:", str(e)[:200])
    return r["access_token"]


def _tt(path, access, body):
    r = http("POST", f"{TT}{path}", raw=json.dumps(body).encode(),
             headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json; charset=UTF-8"})
    err = (r.get("error") or {})
    if err.get("code") not in (None, "ok"):
        raise ApiError(f"TikTok {path} -> {err.get('code')}: {err.get('message', '')[:300]}")
    return r.get("data") or {}


def post_tiktok(item, date, access, workdir):
    info = _tt("/post/publish/creator_info/query/", access, {})
    opts = info.get("privacy_level_options") or []
    privacy = TIKTOK_PRIVACY if TIKTOK_PRIVACY in opts or not opts else "SELF_ONLY"
    f = workdir / item["file"]
    if not f.exists():
        download_asset(date, item["file"], workdir)
    size = f.stat().st_size
    if size > 64 * 1024 * 1024:
        raise ApiError("TikTok: video > 64 MB, chunked upload not implemented")
    d = _tt("/post/publish/video/init/", access, {
        "post_info": {"title": item["caption"][:2200], "privacy_level": privacy,
                      "disable_duet": False, "disable_comment": False, "disable_stitch": False,
                      "video_cover_timestamp_ms": 1000, "is_aigc": True,
                      "brand_content_toggle": False, "brand_organic_toggle": bool(item.get("cta"))},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
    put = urllib.request.Request(d["upload_url"], data=f.read_bytes(), method="PUT",
                                 headers={"Content-Type": "video/mp4", "Content-Length": str(size),
                                          "Content-Range": f"bytes 0-{size - 1}/{size}"})
    try:
        urllib.request.urlopen(put, timeout=600).read()
    except urllib.error.HTTPError as e:
        raise ApiError(f"TikTok upload -> {e.code}: {e.read().decode(errors='replace')[:300]}") from None
    pid = d["publish_id"]
    for _ in range(24):  # wait up to ~2 min for TikTok to process
        time.sleep(5)
        st = _tt("/post/publish/status/fetch/", access, {"publish_id": pid})
        if st.get("status") == "PUBLISH_COMPLETE":
            ids = st.get("publicaly_available_post_id") or st.get("publicly_available_post_id") or []
            return str(ids[0]) if ids else pid
        if st.get("status") == "FAILED":
            raise ApiError(f"TikTok publish failed: {st.get('fail_reason', '?')}")
    return pid  # still processing; TikTok finishes it on its side


# ---------------------------------------------------------------- promo
def promo_for(date):
    p = json.loads((ROOT / "marketing" / "promo-posts.json").read_text())
    if not p.get("enabled", True):
        return None
    start = dt.date.fromisoformat(p["start_date"])
    if date < start:
        return None
    i = (date - start).days % len(p["posts"])
    text = p["posts"][i].replace("{link}", p["link"])
    imgs = p.get("images") or []
    th = re.sub(r"\s*#\w+", "", text).rstrip() + "\n\n#tienganh"
    if len(th) > 480:  # keep first line, price/link line and tag
        lines = [l for l in th.split("\n") if l.strip()]
        keep = [lines[0]] + [l for l in lines if "99.000" in l or "http" in l] + ["#tienganh"]
        th = "\n\n".join(dict.fromkeys(keep))
    return {"time": p["time"], "fb_text": text, "image": imgs[i] if i < len(imgs) else "", "threads_text": th[:480]}


# ---------------------------------------------------------------- main
def due(time_str, date, now):
    t = dt.datetime.combine(date, dt.time.fromisoformat(time_str), VN)
    late = (now - t).total_seconds() / 60
    return 0 <= late <= LATE_LIMIT_MIN, late


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--now", help="override current time HH:MM (testing)")
    ap.add_argument("--tiktok-code", default="", help="one-time: code from the TikTok authorisation redirect")
    ap.add_argument("--retry-failed", action="store_true", help="forget earlier failed attempts (e.g. after renewing an expired token)")
    a = ap.parse_args()
    now = dt.datetime.now(VN)
    date = dt.date.fromisoformat(a.date) if a.date else now.date()
    if a.now:
        now = dt.datetime.combine(date, dt.time.fromisoformat(a.now), VN)
    only = set(filter(None, a.only.split(",")))
    want = lambda k: not only or k in only

    meta = env("META_PAGE_TOKEN")
    ig = env("META_PAGE_TOKEN", "IG_USER_ID")
    fb = env("META_PAGE_TOKEN", "FB_PAGE_ID")
    th = env("THREADS_TOKEN", "THREADS_USER_ID")
    yt = env("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
    tt = env("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET")
    if tt and a.tiktok_code:
        tiktok_exchange_code(*tt, a.tiktok_code); return
    if tt:
        try:
            rt = tiktok_refresh_token(tt[1])
        except Exception as e:
            rt = ""; print("TikTok refresh token not readable:", str(e)[:200])
        tt = (*tt, rt) if rt else None
    print("Enabled:", ", ".join(k for k, v in [("instagram", ig), ("facebook", fb), ("threads", th), ("youtube", yt), ("tiktok", tt)] if v) or "none (no secrets set)")
    # connection check: read-only calls that prove each token works, without posting anything
    if th:
        try:
            me = http("GET", f"{THREADS}/{th[1]}?fields=id,username&access_token={urllib.parse.quote(th[0])}")
            print("Threads connected as @" + me.get("username", "?"))
        except Exception as e:
            print("Threads token check FAILED:", str(e)[:300])
    if fb:
        try:
            pg = http("GET", f"{GRAPH}/{fb[1]}?fields=name&access_token={urllib.parse.quote(fb[0])}")
            print("Facebook Page connected:", pg.get("name"))
        except Exception as e:
            print("Facebook token check FAILED:", str(e)[:300])
    if yt:
        try:
            info = http("GET", "https://oauth2.googleapis.com/tokeninfo?access_token=" + yt_access_token(*yt))
            print("YouTube connected, scope:", info.get("scope", "?"))
        except Exception as e:
            print("YouTube token check FAILED:", str(e)[:300])
    if ig:
        try:
            u = http("GET", f"{GRAPH}/{ig[1]}?fields=username&access_token={urllib.parse.quote(ig[0])}")
            print("Instagram connected as @" + u.get("username", "?"))
        except Exception as e:
            print("Instagram token check FAILED:", str(e)[:300])
    if tt:
        try:
            ci = _tt("/post/publish/creator_info/query/", tiktok_access_token(*tt), {})
            print("TikTok connected as @" + str(ci.get("creator_username", "?")), "| privacy:", TIKTOK_PRIVACY)
        except Exception as e:
            print("TikTok token check FAILED:", str(e)[:300])

    workdir = pathlib.Path(tempfile.mkdtemp())
    plan = load_plan(date.isoformat(), workdir)
    log = load_log(date.isoformat(), workdir)
    done = log["posts"]
    if a.retry_failed:
        for k in [k for k, v in done.items() if not v.get("ok")]:
            print("retrying", k); del done[k]
    count = lambda net: sum(1 for k, v in done.items() if k.startswith(net + ":") and v.get("ok"))

    jobs = []  # (key, time, net, fn)
    thin_meta = sum(1 for it in plan["items"] if it["platform"] == "instagram") > len(META_HOURS)
    for it in plan["items"]:
        if it["platform"] == "instagram" and thin_meta and int(it["time"][:2]) not in META_HOURS:
            continue
        if it["platform"] == "instagram":
            if ig and want("instagram"):
                jobs.append((f"instagram:{it['id']}", it["time"], "instagram", lambda it=it: post_instagram(it, date.isoformat(), *ig)))
            if fb and want("facebook"):
                jobs.append((f"facebook:{it['id']}", it["time"], "facebook", lambda it=it: post_facebook_reel(it, date.isoformat(), *fb)))
        elif it["platform"] == "youtube" and yt and want("youtube") and (YT_DAILY_MAX >= 12 or int(it["time"][:2]) in YT_HOURS):
            jobs.append((f"youtube:{it['id']}", it["time"], "youtube", lambda it=it: post_youtube(it, date.isoformat(), yt_tok(), workdir)))
        elif it["platform"] == "tiktok" and tt and want("tiktok") and it["id"] not in _studio_ids():
            jobs.append((f"tiktok:{it['id']}", it["time"], "tiktok", lambda it=it: post_tiktok(it, date.isoformat(), tt_tok(), workdir)))
    for t in plan.get("threads", []):
        if th and want("threads"):
            body = re.sub(r"\n*#\w+\s*$", "", t["text"]).rstrip()  # topic goes in topic_tag, keep text clean
            jobs.append((f"threads:{t['id']}", t["time"], "threads", lambda body=body, t=t: post_threads(body, t["topic"], *th)))
    pr = promo_for(date)
    if pr and want("promo"):
        if fb:
            jobs.append(("facebook-promo:" + date.isoformat(), pr["time"], "facebook-promo", lambda: post_facebook_photo(pr["fb_text"], pr["image"], *fb)))
        if th:
            jobs.append(("threads-promo:" + date.isoformat(), pr["time"], "threads",
                         lambda: post_threads(re.sub(r"\n*#\w+\s*$", "", pr["threads_text"]).rstrip(), "tienganh", *th)))

    for op in one_off_posts(date):
        img = op.get("image", "")
        if op.get("facebook") and fb and want("facebook"):
            jobs.append((f"facebook-post:{op['id']}", op["time"], "facebook-promo", lambda op=op, img=img: post_facebook_photo(op["facebook"], img, *fb)))
        if op.get("instagram") and ig and want("instagram") and img:
            jobs.append((f"instagram-post:{op['id']}", op["time"], "instagram", lambda op=op, img=img: post_instagram_image(op["instagram"], img, *ig)))
        if op.get("threads") and th and want("threads"):
            jobs.append((f"threads-post:{op['id']}", op["time"], "threads",
                         (lambda op=op, img=img: post_threads_image(op["threads"], img, op.get("topic", ""), *th)) if img
                         else (lambda op=op: post_threads(op["threads"], op.get("topic", ""), *th))))

    _tt_tok = {}
    def tt_tok():
        if "t" not in _tt_tok:
            _tt_tok["t"] = tiktok_access_token(*tt)
        return _tt_tok["t"]

    _yt = {}
    def yt_tok():
        if "t" not in _yt:
            _yt["t"] = yt_access_token(*yt)
        return _yt["t"]

    posted = errors = 0
    for key, tm, net, fn in sorted(jobs, key=lambda j: j[1]):
        if key in done and done[key].get("ok"):
            continue
        is_due, late = due(tm, date, now)
        if not is_due:
            if late > LATE_LIMIT_MIN and key not in done:
                done[key] = {"ok": False, "skipped": f"more than {LATE_LIMIT_MIN} min late"}
            continue
        if net == "youtube" and count("youtube") >= YT_DAILY_MAX:
            done.setdefault(key, {"ok": False, "skipped": f"YouTube daily cap {YT_DAILY_MAX} (API quota)"}); continue
        if net == "facebook" and count("facebook") >= FB_DAILY_MAX:
            done.setdefault(key, {"ok": False, "skipped": "Facebook 30 reels/24h"}); continue
        if (done.get(key) or {}).get("tries", 0) >= 2:
            continue
        print(f"→ {key} ({tm})", end=" ")
        if a.dry_run:
            print("[dry-run]"); continue
        try:
            pid = fn()
            done[key] = {"ok": True, "id": str(pid), "at": dt.datetime.now(VN).isoformat(timespec="seconds")}
            posted += 1; print("OK", pid)
        except Exception as e:  # record and continue with the next post
            prev = done.get(key) or {}
            done[key] = {"ok": False, "error": str(e)[:500], "tries": prev.get("tries", 0) + 1}
            errors += 1; print("ERROR", str(e)[:300])
        save_log(date.isoformat(), log, workdir)  # after every post, so a crash never causes a repost
    print(f"Posted {posted}, errors {errors}, total ok today: {sum(1 for v in done.values() if v.get('ok'))}")
    if not a.dry_run:
        save_log(date.isoformat(), log, workdir)
        try:
            write_status(date, now, plan, jobs, done, pr)
        except Exception as e:  # the status table is a convenience; never fail the run for it
            print("status table not written:", str(e)[:300])


# ---------------------------------------------------------------- live status for the Hub
STATUS_BRANCH = "status"
NET_VI = {"instagram": "Instagram", "facebook": "Facebook", "facebook-promo": "Facebook", "threads": "Threads",
          "youtube": "YouTube", "tiktok": "TikTok"}


def _title(it):
    t = (it.get("terms") or [{}])[0]
    return f"{t.get('term', '')} — {it.get('discipline_en', '')}".strip(" —") or it.get("title", "")


def fetch_views(done):
    """Current views of today's posted items, read from each platform's own API (Metricool lags a day).
    Returns {key: views}. A platform whose token lacks the insights permission is reported once and skipped."""
    out, failed = {}, set()
    tok, th_tok = os.environ.get("META_PAGE_TOKEN"), os.environ.get("THREADS_TOKEN")
    yt, yt_access = env("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"), None
    yt_ids = {}
    for key, rec in done.items():
        net, pid = key.split(":", 1)[0], str(rec.get("id") or "")
        if not rec.get("ok") or not pid or net in failed:
            continue
        try:
            if net == "instagram" and tok:
                r = http("GET", f"{GRAPH}/{pid}/insights?metric=views&access_token={urllib.parse.quote(tok)}", timeout=20)
                out[key] = int(r["data"][0]["values"][0]["value"])
            elif net == "facebook" and tok:
                r = http("GET", f"{GRAPH}/{pid}/video_insights?metric=blue_reels_play_count&access_token={urllib.parse.quote(tok)}", timeout=20)
                out[key] = int(r["data"][0]["values"][0]["value"])
            elif net == "threads" and th_tok:
                r = http("GET", f"{THREADS}/{pid}/insights?metric=views&access_token={urllib.parse.quote(th_tok)}", timeout=20)
                out[key] = int(r["data"][0]["values"][0]["value"])
            elif net == "youtube" and yt:
                yt_ids[pid] = key
        except Exception as e:
            failed.add(net); print(f"views not readable for {net}:", str(e)[:200])
    if yt_ids:
        try:
            yt_access = yt_access_token(*yt)
            req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=statistics&id=" + ",".join(yt_ids),
                                         headers={"Authorization": f"Bearer {yt_access}"})
            with urllib.request.urlopen(req, timeout=20) as r:
                for v in json.loads(r.read().decode()).get("items", []):
                    out[yt_ids[v["id"]]] = int(v["statistics"].get("viewCount", 0))
        except Exception as e:
            print("views not readable for youtube via API:", str(e)[:200])
    # No read permission on the token: read the public view count from each Short's own page instead.
    for pid, key in yt_ids.items():
        if key in out:
            continue
        try:
            req = urllib.request.Request(f"https://www.youtube.com/watch?v={pid}&hl=en",
                                         headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", "replace")
            m = re.search(r'"viewCount":"(\d+)"', html) or re.search(r'"viewCount":\{"simpleText":"([\d,.]+)', html)
            if m:
                out[key] = int(m.group(1).replace(",", "").replace(".", ""))
        except Exception as e:
            print("public YouTube views not read:", str(e)[:120]); break
    print("views read for", len(out), "posts")
    return out


def tiktok_views():
    """TikTok has no API for this account; the autopilot reads TikTok Studio and stores
    {"updated": "...", "views": {"<term>": n}} in status/tiktok-views.json on the status branch."""
    try:
        import base64
        r = gh("api", f"repos/{REPO}/contents/status/tiktok-views.json?ref={STATUS_BRANCH}", check=False)
        if r.returncode != 0:
            return {}
        d = json.loads(base64.b64decode(json.loads(r.stdout)["content"]).decode())
        return {str(k).strip().lower(): v for k, v in (d.get("views") or {}).items()}
    except Exception as e:
        print("TikTok views not read:", str(e)[:200]); return {}


def status_rows(date, now, plan, jobs, done, pr):
    """One row per post planned today on every platform: posted / pending / error / skipped."""
    try:
        views = fetch_views(done)
    except Exception as e:
        views = {}; print("views not read:", str(e)[:200])
    titles = {it["id"]: _title(it) for it in plan["items"]}
    one_titles = {op["id"]: op.get("title", op["id"]) for op in one_off_posts(date)}
    for t in plan.get("threads", []):
        titles[t["id"]] = (t["text"].split("\n")[0])[:90]
    rows = []
    for key, tm, net, _fn in jobs:
        kind, _, ident = key.partition(":")
        rec = done.get(key) or {}
        if rec.get("ok"):
            st, detail = "posted", rec.get("at", "")[11:16]
        elif rec.get("skipped"):
            st, detail = "skipped", rec["skipped"]
        elif rec.get("error"):
            st, detail = ("error" if rec.get("tries", 0) >= 2 else "retry"), rec["error"][:140]
        else:
            st, detail = "pending", ""
        title = titles.get(ident) or (one_titles.get(ident)) or ("Bài quảng bá có ảnh" if kind == "facebook-promo" else "Bài quảng bá" if kind == "threads-promo" else ident)
        kind_vi = {"facebook-post": "Bài ảnh", "instagram-post": "Bài ảnh", "threads-post": "Bài ảnh",
                   "facebook": "Reel", "facebook-promo": "Ảnh quảng bá", "threads-promo": "Quảng bá", "instagram": "Reel",
                   "youtube": "Short", "threads": "Bài viết", "tiktok": "Video"}.get(kind, kind)
        rows.append([date.isoformat(), tm, NET_VI.get(net, net), kind_vi, title, st, detail, rec.get("id", ""), views.get(key, "")])
    # YouTube Shorts left out by the daily API quota still show, so the Hub can count all 12 disciplines.
    keys = {j[0] for j in jobs}
    for it in plan["items"]:
        if it["platform"] == "youtube" and f"youtube:{it['id']}" not in keys:
            rows.append([date.isoformat(), it["time"], "YouTube", "Short", _title(it), "skipped",
                         f"vượt hạn mức {YT_DAILY_MAX} Short/ngày (quota YouTube API)", ""])
    # TikTok is scheduled in TikTok Studio; it publishes itself at the scheduled time.
    studio = _studio_ids()
    tk_views = tiktok_views()
    for it in plan["items"]:
        if it["platform"] != "tiktok" or f"tiktok:{it['id']}" in keys:
            continue
        t = dt.datetime.combine(date, dt.time.fromisoformat(it["time"]), VN)
        if it["id"] in studio:
            st, detail = ("posted", "TikTok Studio") if now >= t else ("pending", "đã hẹn giờ trên TikTok Studio")
        else:
            st, detail = ("error", "chưa hẹn giờ trên TikTok Studio") if now >= t else ("pending", "chưa hẹn giờ")
        term = ((it.get("terms") or [{}])[0].get("term") or "").strip().lower()
        rows.append([date.isoformat(), it["time"], "TikTok", "Video", _title(it), st, detail, "", tk_views.get(term, "") if st == "posted" else ""])
    rows.sort(key=lambda r: (r[1], r[2]))
    return rows


def _studio_ids():
    try:
        return set(json.loads((ROOT / "marketing" / "tiktok-studio-scheduled.json").read_text())["ids"])
    except Exception:
        return set()


def planned_rows(date, plan):
    """Tomorrow's plan as status rows (nothing posted yet), so the Hub can show the next day."""
    studio, rows = _studio_ids(), []
    for it in plan.get("items", []):
        d, tm, title = date.isoformat(), it["time"], _title(it)
        if it["platform"] == "instagram":
            rows += [[d, tm, "Instagram", "Reel", title, "planned", "", ""], [d, tm, "Facebook", "Reel", title, "planned", "", ""]]
        elif it["platform"] == "youtube":
            capped = YT_DAILY_MAX < 12 and int(tm[:2]) not in YT_HOURS
            rows.append([d, tm, "YouTube", "Short", title, "skipped" if capped else "planned",
                         f"vượt hạn mức {YT_DAILY_MAX} Short/ngày (quota YouTube API)" if capped else "", ""])
        elif it["platform"] == "tiktok":
            rows.append([d, tm, "TikTok", "Video", title, "planned",
                         "đã hẹn giờ trên TikTok Studio" if it["id"] in studio else
                         ("tự đăng qua TikTok API" if os.environ.get("TIKTOK_CLIENT_KEY") else "chưa có khoá TikTok API"), ""])
    for t in plan.get("threads", []):
        rows.append([date.isoformat(), t["time"], "Threads", "Bài viết", (t["text"].split("\n")[0])[:90], "planned", "", ""])
    rows.sort(key=lambda r: (r[1], r[2]))
    return rows


def _csv(rows):
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "time", "platform", "kind", "title", "status", "detail", "post_id", "views"])
    w.writerows(rows)
    w.writerow(["_updated", dt.datetime.now(VN).strftime("%Y-%m-%d %H:%M"), "", "", "", "", "", "", ""])
    return buf.getvalue()


def _put_file(path, text, message):
    import base64
    r = gh("api", f"repos/{REPO}/contents/{path}?ref={STATUS_BRANCH}", check=False)
    sha = json.loads(r.stdout).get("sha") if r.returncode == 0 else None
    body = {"message": message, "branch": STATUS_BRANCH, "content": base64.b64encode(text.encode()).decode()}
    if sha:
        body["sha"] = sha
    tmp = pathlib.Path(tempfile.mkstemp(suffix=".json")[1])
    tmp.write_text(json.dumps(body))
    gh("api", "-X", "PUT", f"repos/{REPO}/contents/{path}", "--input", str(tmp))


def write_status(date, now, plan, jobs, done, pr):
    r = gh("api", f"repos/{REPO}/git/ref/heads/{STATUS_BRANCH}", check=False)
    if r.returncode != 0:  # first run: create the branch from main
        main_sha = json.loads(gh("api", f"repos/{REPO}/git/ref/heads/main").stdout)["object"]["sha"]
        gh("api", "-X", "POST", f"repos/{REPO}/git/refs", "-f", f"ref=refs/heads/{STATUS_BRANCH}", "-f", f"sha={main_sha}")
    rows = status_rows(date, now, plan, jobs, done, pr)
    try:  # tomorrow's plan exists once the evening render (18:00) has published it
        nxt = date + dt.timedelta(days=1)
        rel = _release(nxt.isoformat())
        wd = pathlib.Path(tempfile.mkdtemp())
        if rel and _download(rel, "plan.json", wd):
            rows += planned_rows(nxt, json.loads((wd / "plan.json").read_text()))
    except Exception as e:
        print("tomorrow's plan not added:", str(e)[:200])
    text = _csv(rows)
    _put_file("status/today.csv", text, f"status {date} {now:%H:%M}")
    print("Hub status table updated:", text.count("\n") - 2, "posts")


if __name__ == "__main__":
    main()

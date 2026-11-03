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


# ---------------------------------------------------------------- promo
def promo_for(date):
    p = json.loads((ROOT / "marketing" / "promo-posts.json").read_text())
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
    print("Enabled:", ", ".join(k for k, v in [("instagram", ig), ("facebook", fb), ("threads", th), ("youtube", yt)] if v) or "none (no secrets set)")
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
    if ig:
        try:
            u = http("GET", f"{GRAPH}/{ig[1]}?fields=username&access_token={urllib.parse.quote(ig[0])}")
            print("Instagram connected as @" + u.get("username", "?"))
        except Exception as e:
            print("Instagram token check FAILED:", str(e)[:300])

    workdir = pathlib.Path(tempfile.mkdtemp())
    plan = load_plan(date.isoformat(), workdir)
    log = load_log(date.isoformat(), workdir)
    done = log["posts"]
    count = lambda net: sum(1 for k, v in done.items() if k.startswith(net + ":") and v.get("ok"))

    jobs = []  # (key, time, net, fn)
    for it in plan["items"]:
        if it["platform"] == "instagram":
            if ig and want("instagram"):
                jobs.append((f"instagram:{it['id']}", it["time"], "instagram", lambda it=it: post_instagram(it, date.isoformat(), *ig)))
            if fb and want("facebook"):
                jobs.append((f"facebook:{it['id']}", it["time"], "facebook", lambda it=it: post_facebook_reel(it, date.isoformat(), *fb)))
        elif it["platform"] == "youtube" and yt and want("youtube"):
            jobs.append((f"youtube:{it['id']}", it["time"], "youtube", lambda it=it: post_youtube(it, date.isoformat(), yt_tok(), workdir)))
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


if __name__ == "__main__":
    main()

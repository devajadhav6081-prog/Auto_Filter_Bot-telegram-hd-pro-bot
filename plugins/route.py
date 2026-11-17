from aiohttp import web
import re
import math
import logging
import secrets
import mimetypes
from aiohttp.http_exceptions import BadStatusLine
from dreamxbotz.Bot import multi_clients, work_loads
from dreamxbotz.server.exceptions import FIleNotFound, InvalidHash
from dreamxbotz.util.custom_dl import ByteStreamer
from dreamxbotz.util.render_template import render_page
from utils import temp
import info

logger = logging.getLogger(__name__)


routes = web.RouteTableDef()

@routes.get("/favicon.ico")
async def favicon_route_handler(request):
    return web.FileResponse('dreamxbotz/template/favicon.ico')

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("dreamxbotz")


@routes.get("/app", allow_head=True)
async def custom_menu_handler(request: web.Request):
    html = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#10131d"><title>Auto Filter Bot Menu</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root{color-scheme:dark;--text:var(--tg-theme-text-color,#f4f6ff);--muted:var(--tg-theme-hint-color,#aab1c5);--panel:rgba(255,255,255,.075);--line:rgba(255,255,255,.15)}
*{box-sizing:border-box}body{margin:0;min-height:100vh;padding:26px 18px 34px;background:radial-gradient(circle at 15% 0%,#273a65 0,transparent 38%),radial-gradient(circle at 100% 100%,#49265d 0,transparent 38%),var(--tg-theme-bg-color,#10131d);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:520px;margin:auto}.top{text-align:center;padding:12px 8px 24px}.logo{width:68px;height:68px;margin:0 auto 14px;border-radius:22px;display:grid;place-items:center;font-size:34px;background:linear-gradient(135deg,#6b8cff,#b66bff);box-shadow:0 12px 34px #6b8cff45}.eyebrow{font-size:11px;letter-spacing:3px;color:var(--muted)}h1{font-size:25px;margin:8px 0 6px}.sub{font-size:13px;color:var(--muted);margin:0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.item{min-height:112px;border:1px solid var(--line);border-radius:20px;padding:18px 14px;text-align:left;color:var(--text);background:var(--panel);backdrop-filter:blur(18px);box-shadow:0 8px 28px #0002;cursor:pointer;font:inherit;transition:transform .15s,border-color .15s}.item:active{transform:scale(.97)}.item:first-child{grid-column:1/-1;min-height:92px;background:linear-gradient(120deg,#5478df33,#a35be533)}.ico{display:block;font-size:25px;margin-bottom:10px}.name{display:block;font-weight:750;font-size:14px;letter-spacing:.5px}.desc{display:block;font-size:11px;color:var(--muted);margin-top:4px}.footer{text-align:center;color:var(--muted);font-size:11px;margin-top:24px}
</style></head><body><div class="wrap">
<header class="top"><div class="logo">🎬</div><div class="eyebrow">WELCOME TO</div><h1>AUTO FILTER BOT</h1><p class="sub">Choose an option to continue</p></header>
<main class="grid">
<button class="item" onclick="addGroup()"><span class="ico">➕</span><span class="name">ADD ME TO YOUR GROUP</span><span class="desc">Add the bot to your Telegram group</span></button>
<button class="item" onclick="sendAction('help')"><span class="ico">📢</span><span class="name">HELP</span><span class="desc">How to use the bot</span></button>
<button class="item" onclick="sendAction('about')"><span class="ico">📖</span><span class="name">ABOUT</span><span class="desc">Bot information</span></button>
<button class="item" onclick="sendAction('topsearch')"><span class="ico">⭐</span><span class="name">TOP SEARCHING</span><span class="desc">Popular searches</span></button>
<button class="item" onclick="sendAction('premium')"><span class="ico">🎟️</span><span class="name">UPGRADE</span><span class="desc">View available plans</span></button>
</main><div class="footer">Secure • Simple • Fast</div></div>
<script>const tg=window.Telegram?.WebApp;if(tg){tg.ready();tg.expand();}
function sendAction(action){if(tg){tg.sendData(action);}else{alert('Please open this menu from the bot in Telegram.');}}
function addGroup(){window.location.href='https://t.me/__BOT_USERNAME__?startgroup=true';}</script>
</body></html>"""
    html = html.replace("__BOT_USERNAME__", temp.U_NAME or "")
    return web.Response(text=html, content_type="text/html")

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(text=await render_page(id, secure_hash), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            id = int(match.group(2))
        else:
            # Try to extract ID from path
            id_match = re.search(r"(\d+)(?:\/\S+)?", path)
            if not id_match:
                # Path doesn't contain any numeric ID - return 404
                raise web.HTTPNotFound(text="Not found")
            id = int(id_match.group(1))
            secure_hash = request.rel_url.query.get("hash")
        
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except web.HTTPNotFound:
        raise  # Re-raise HTTPNotFound without logging
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(e.with_traceback(None))
        raise web.HTTPInternalServerError(text=str(e))

class_cache = {}

async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]
    
    if info.MULTI_CLIENT:
        logger.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logger.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logger.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
    file_id = await tg_connect.get_file_properties(id)
    
    if file_id.unique_id[:6] != secure_hash:
        logger.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash
    
    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )
    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil((until_bytes + 1) / chunk_size) - math.floor(offset / chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name

    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)[0] or "application/octet-stream"
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"
    
    resp_headers = {
        "Content-Type": f"{mime_type}",
        "Content-Length": str(req_length),
        "Content-Disposition": f'inline; filename="{file_name}"',
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Range, Content-Type",
        "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
    }
    
    if range_header:
        resp_headers["Content-Range"] = f"bytes {from_bytes}-{until_bytes}/{file_size}"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers=resp_headers
    )

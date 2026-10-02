"""Harper Rail single-user Korail commuter watcher.

No CAPTCHA / anti-bot bypass. A Korail block or uncertain reservation response
stops the job. Never stores user Korail credentials in website or Git history.
"""
from __future__ import annotations
import json, os, re, threading, time, hmac, urllib.request, urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

KST=ZoneInfo('Asia/Seoul')
SECRET=os.getenv('DASHBOARD_TOKEN','')
KORAIL_ID=os.getenv('KORAIL_ID','')
KORAIL_PASSWORD=os.getenv('KORAIL_PASSWORD','')
INTERVAL=max(10,int(os.getenv('POLL_SECONDS','60')))
LIVE=os.getenv('ENABLE_LIVE_RESERVATION','false').lower()=='true'
ALLOWED_ORIGIN=os.getenv('FRONTEND_ORIGIN','https://harperddol.github.io').rstrip('/')
LOCK=threading.RLock()
STATE={"status":"idle","note":"설정 전","checks":0,"last_check":None,"train":None,"hold":None,"config":None}
WORKER=None
STOP=threading.Event()

class StopWatching(Exception): pass

def update(**kwargs):
    with LOCK: STATE.update(kwargs)

def snapshot():
    with LOCK: return dict(STATE)

def normalize_config(payload):
    obj={k: str(payload.get(k,'')).strip() for k in ('departure','arrival','date','train_no','seat')}
    if obj['departure']==obj['arrival'] or obj['departure'] not in ['대전','수서','서울','동대구','부산','천안아산','광명'] or obj['arrival'] not in ['대전','수서','서울','동대구','부산','천안아산','광명']:
        raise ValueError('출발역과 도착역을 확인해 주세요.')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',obj['date']): raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다.')
    day=datetime.strptime(obj['date'],'%Y-%m-%d').date(); now=datetime.now(KST).date()
    if day<now or day>now+timedelta(days=31): raise ValueError('탑승일은 오늘부터 31일 이내여야 합니다.')
    if not re.fullmatch(r'\d{1,5}',obj['train_no']): raise ValueError('열차번호를 숫자로 입력해 주세요.')
    if obj['seat'] not in ('both','standard','first'): raise ValueError('좌석등급을 선택해 주세요.')
    obj['time']=str(payload.get('time','00:00'))
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',obj['time']): raise ValueError('출발시간을 확인해 주세요.')
    obj['consent']=payload.get('consent') is True
    if not obj['consent']: raise ValueError('실제 좌석 1석 예약에 동의해야 합니다.')
    return obj

def normalize_search(payload):
    # Read-only timetable search. Does not create a hold or booking.
    dep=str(payload.get('departure','')).strip()
    arr=str(payload.get('arrival','')).strip()
    day=str(payload.get('date','')).strip()
    start=str(payload.get('time','')).strip()
    if dep==arr or dep not in ['대전','수서','서울','동대구','부산','천안아산','광명'] or arr not in ['대전','수서','서울','동대구','부산','천안아산','광명']:
        raise ValueError('출발역과 도착역을 확인해 주세요.')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day): raise ValueError('탑승 날짜를 확인해 주세요.')
    date_obj=datetime.strptime(day,'%Y-%m-%d').date()
    if date_obj<datetime.now(KST).date() or date_obj>datetime.now(KST).date()+timedelta(days=31):
        raise ValueError('조회 날짜는 오늘부터 31일 이내여야 합니다.')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',start): raise ValueError('출발 시간을 확인해 주세요.')
    return {'departure':dep,'arrival':arr,'date':day,'time':start}

def time_string(val):
    # Some clients return HHMMSS, some return datetime or HH:MM.
    raw=str(val or '')
    if re.fullmatch(r'\d{6}',raw): return raw[:2]+':'+raw[2:4]
    if re.fullmatch(r'\d{4}',raw): return raw[:2]+':'+raw[2:]
    if re.fullmatch(r'\d{2}:\d{2}.*',raw): return raw[:5]
    return raw[:24]

def trains_preview(conf):
    from korail_mobile_api import KorailClient, TrainSearchQuery
    # The timetable endpoint is a documented read-only operation and does not
    # require a Korail account session. Do not perform a login for a preview:
    # login can trigger the separate DynaPath anti-automation gate.
    # If the public read itself is refused, report the error and stop.
    client=KorailClient()
    try:
        query=TrainSearchQuery(conf['departure'],conf['arrival'],conf['date'].replace('-',''),departure_time=conf['time'].replace(':','')+'00',passengers=1)
        result=client.search_trains(query)
        trains=list(result.trains)
        # One follow-on page at most, avoiding large repeated requests.
        cont=result.next_page()
        if cont is not None and len(trains)<15:
            extra=client.search_trains(query,continuation=cont)
            trains+=list(extra.trains)
        data=[];seen=set()
        for t in trains[:30]:
            no=str(getattr(t,'train_no','')).strip()
            depart=time_string(getattr(t,'departure_time',''))
            arrive=time_string(getattr(t,'arrival_time',''))
            if not re.fullmatch(r'\d{1,5}',no): continue
            if (no,depart) in seen: continue
            seen.add((no,depart))
            data.append({'train_no':no,'departure_time':depart,'arrival_time':arrive,
                         'train_type':str(getattr(t,'train_type_name','') or getattr(t,'train_type','') or '열차')[:45],
                         'general':str(getattr(t,'general_availability_name','') or '정보 없음')[:45],
                         'special':str(getattr(t,'special_availability_name','') or '정보 없음')[:45]})
        return {'ok':True,'trains':data,'source':'unofficial_live_search','note':'비공식 코레일 연동 결과이며 잔여석은 실시간으로 달라질 수 있습니다.'}
    finally:
        try:client.close()
        except Exception: pass

def has_available(train, seat):
    label=str(getattr(train,('special_availability_name' if seat=='first' else 'general_availability_name'), '') or '')
    if any(x in label for x in ['매진','없음','불가','예약대기','입석']): return False
    return any(x in label for x in ['예약','가능','여유'])

def verify_existing(client):
    """Conservative duplicate protection. Unknown reservation state is fatal."""
    return client.get_reservation_history()

def notify(message):
    token=os.getenv('TELEGRAM_BOT_TOKEN',''); chat=os.getenv('TELEGRAM_CHAT_ID','')
    if not (token and chat): return
    try:
        data=urllib.parse.urlencode({'chat_id':chat,'text':message}).encode()
        urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=data),timeout=8).close()
    except Exception: pass

def run_job(conf):
    client=None
    try:
        from korail_mobile_api import KorailClient, TrainSearchQuery, MutationConsent, KorailPassengerCounts, KorailSeatClass
        if not KORAIL_ID or not KORAIL_PASSWORD: raise StopWatching('Railway 환경변수 KORAIL_ID / KORAIL_PASSWORD 미설정')
        # If a real service requires anti-automation challenges, fail rather than bypass.
        client=KorailClient()
        client.login(KORAIL_ID,KORAIL_PASSWORD)
        update(status='watching',note='코레일 접속 성공, 조회 중')
        while not STOP.is_set():
            if datetime.now(KST).date() > datetime.strptime(conf['date'],'%Y-%m-%d').date():
                raise StopWatching('탑승일이 지나 감시를 종료했습니다.')
            try:
                query=TrainSearchQuery(conf['departure'], conf['arrival'], conf['date'].replace('-',''), departure_time=conf['time'].replace(':','')+'00',passengers=1)
                result=client.search_trains(query)
                trains=list(result.trains)
                # Only search a few pages, never flood; exact train id must match.
                cont=result.next_page()
                for _ in range(2):
                    if any(str(t.train_no).lstrip('0') == conf['train_no'].lstrip('0') for t in trains) or cont is None: break
                    result=client.search_trains(query,continuation=cont)
                    trains+=list(result.trains)
                    cont=result.next_page()
                matching=[t for t in trains if str(t.train_no).lstrip('0')==conf['train_no'].lstrip('0')]
                update(last_check=datetime.now(KST).isoformat(timespec='seconds'),checks=snapshot()['checks']+1,train=conf['train_no'])
                if matching:
                    train=matching[0]
                    for seat in (['standard','first'] if conf['seat']=='both' else [conf['seat']]):
                        if not has_available(train,seat): continue
                        if not LIVE: raise StopWatching('좌석 가능 표시 발견. 서버의 ENABLE_LIVE_RESERVATION이 꺼져 있어 실제 예약은 진행하지 않았습니다.')
                        # Duplicates are costly: check existing state before mutation.
                        verify_existing(client)
                        seatclass=KorailSeatClass.SPECIAL if seat=='first' else KorailSeatClass.GENERAL
                        # Mark 'uncertain' first; do not retry any mutation on error.
                        update(status='uncertain',note='예약 요청 중: 중복 방지를 위해 자동 재시도 안 함')
                        hold=client.reserve(train,consent=MutationConsent(allow_reserve=True,dry_run=False),passengers=KorailPassengerCounts(adult=1),seat_class=seatclass)
                        update(status='reserved',note='예약 요청 응답 수신. 코레일+에서 즉시 예약 내역과 결제 마감시간 확인',hold=str(getattr(hold,'pnr_no',''))[-8:] or '코레일 내역 확인')
                        notify('Harper Rail: 열차 예약 응답을 받았습니다. 코레일+에서 즉시 예약 내역과 결제기한을 확인하세요.')
                        STOP.set()
                        return
                update(status='watching',note=('열차 조회 완료; 대상열차 '+ ('확인' if matching else '검색 결과 없음') + ' · 다음 조회 대기'))
            except Exception as exc:
                # Do not automatically retry authentication / protocol / seat mutations.
                name=type(exc).__name__
                if any(k in name.lower() for k in ['soldout','seatunavailable']):
                    update(status='watching',note='좌석 선점 또는 매진; 다음 조회 대기')
                else:
                    raise StopWatching(f'조회/연동 오류로 중지됨 ({name}). 코레일 공식 앱에서 확인하세요.')
            STOP.wait(INTERVAL)
        if snapshot()['status'] not in ('reserved','uncertain'): update(status='stopped',note='사용자 요청으로 중단됨')
    except StopWatching as exc:
        if snapshot()['status']!='uncertain': update(status='stopped',note=str(exc))
        notify('Harper Rail 감시 중단: '+str(exc))
    except Exception as exc:
        update(status='stopped',note=f'연동 실패: {type(exc).__name__}. 공식 앱에서 확인하세요.')
        notify('Harper Rail 연동 실패. 코레일 공식 앱에서 확인하세요.')
    finally:
        if client:
            try: client.close()
            except Exception: pass

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt,*args): pass
    def send_json(self, data, code=200):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Access-Control-Allow-Origin',ALLOWED_ORIGIN)
        self.send_header('Vary','Origin')
        self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self.send_json({})
    def authorized(self):
        received=self.headers.get('Authorization','')
        return bool(SECRET) and hmac.compare_digest(received,'Bearer '+SECRET)
    def do_GET(self):
        if self.path=='/health': return self.send_json({'ok':True,'service':'Harper Rail backend','live_booking_enabled':LIVE})
        if not self.authorized(): return self.send_json({'error':'인증이 필요합니다'},401)
        if self.path=='/status': return self.send_json({**snapshot(),'interval_seconds':INTERVAL,'live_booking_enabled':LIVE})
        self.send_json({'error':'경로 없음'},404)
    def do_POST(self):
        global WORKER
        if not self.authorized(): return self.send_json({'error':'인증이 필요합니다'},401)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>4096: return self.send_json({'error':'요청 크기 초과'},413)
            body=json.loads(self.rfile.read(n) or b'{}')
            if self.path=='/trains':
                conf=normalize_search(body)
                try:
                    result=trains_preview(conf)
                    return self.send_json(result)
                except Exception as exc:
                    # Never leak credentials or upstream response bodies to the browser.
                    return self.send_json({'error':'코레일 열차 조회 실패 ('+type(exc).__name__+'). 공식 앱과 Railway 서버 로그를 확인하세요.'},502)
            if self.path=='/stop':
                STOP.set(); return self.send_json({'ok':True,'note':'중지 요청됨'})
            if self.path!='/start': return self.send_json({'error':'경로 없음'},404)
            conf=normalize_config(body)
            with LOCK:
                if WORKER is not None and WORKER.is_alive(): return self.send_json({'error':'이미 감시 중입니다. 먼저 중지해 주세요.'},409)
                if snapshot()['status']=='uncertain': return self.send_json({'error':'예약 결과가 불확실합니다. 코레일 예약 내역을 확인해야 재시작할 수 있습니다.'},409)
                STOP.clear()
                update(status='starting',note='코레일 로그인 시도 중',checks=0,last_check=None,train=conf['train_no'],hold=None,config={k:v for k,v in conf.items() if k!='consent'})
                WORKER=threading.Thread(target=run_job,args=(conf,),daemon=True); WORKER.start()
            self.send_json({'ok':True,'note':'감시 프로세스 시작 요청됨. 실제 연결 상태는 status에서 확인하세요.'})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc: self.send_json({'error':str(exc)},400)

if __name__=='__main__':
    if not SECRET: raise SystemExit('DASHBOARD_TOKEN 환경변수를 먼저 설정하세요')
    port=int(os.environ.get('PORT','8080'))
    print(f'Harper Rail backend listening on :{port} (live booking={LIVE})',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()

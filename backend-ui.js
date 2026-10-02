'use strict';
(()=>{
  const $=id=>document.getElementById(id);
  const saved=localStorage.getItem('harper-server-url')||'';
  $('backendUrl').value=saved;
  let timer=null;
  const setStatus=message=>{$('backendStatus').textContent=message;};
  function creds(){
    const base=$('backendUrl').value.trim().replace(/\/+$/,'');
    if(!/^https:\/\/[a-z0-9.-]+(?::\d+)?$/i.test(base)) throw Error('https://로 시작하는 Railway 서버 주소를 입력해 주세요.');
    const token=$('backendToken').value.trim();
    if(!token) throw Error('개인 대시보드 토큰을 입력하세요.');
    localStorage.setItem('harper-server-url',base);
    return {base,token};
  }
  async function request(path,body){
    const {base,token}=creds();
    const res=await fetch(base+path,{method:body?'POST':'GET',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,cache:'no-store'});
    const data=await res.json();
    if(!res.ok) throw Error(data.error||`서버 오류 ${res.status}`);
    return data;
  }
  async function refresh(){try{
    const s=await request('/status');
    const latest=s.last_check?`최근 조회: ${s.last_check}`:'아직 조회하지 않음';
    setStatus(`상태: ${s.status} | ${s.note} | 조회 ${s.checks}회 | ${latest} | 예약 기능 ${s.live_booking_enabled?'활성':'비활성'}`);
    if(['reserved','stopped','uncertain','idle'].includes(s.status) && timer){clearInterval(timer);timer=null;}
  }catch(e){setStatus('연결 실패: '+e.message);}}
  $('backendStart').addEventListener('click',async()=>{
    try{
      if(!$('bookingConsent').checked)throw Error('실제 1석 예약 동의에 체크해 주세요.');
      if($('count').value!=='1')throw Error('자동 감시는 성인 1명만 지원합니다.');
      const req={departure:$('from').value,arrival:$('to').value,date:$('date').value,time:$('time').value,train_no:$('train').value.trim(),seat:$('class').value,consent:true};
      setStatus('서버에 감시 시작을 요청하는 중…');
      const response=await request('/start',req);setStatus(response.note);
      if(timer) clearInterval(timer);timer=setInterval(refresh,10000);await refresh();
    }catch(e){setStatus('시작 실패: '+e.message);}
  });
  $('backendStop').addEventListener('click',async()=>{try{const r=await request('/stop',{});setStatus(r.note);await refresh();}catch(e){setStatus('중지 실패: '+e.message);}});
  $('backendRefresh').addEventListener('click',refresh);
})();
